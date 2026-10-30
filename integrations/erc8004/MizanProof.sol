// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MizanProof: refuse capital to anything unproven, in one line.
/// @notice Verifies a MIZAN passport receipt (EIP-712) with one ecrecover. No oracle, no call to MIZAN, and nothing
///         deployed by MIZAN: import this library into your own contract and it works on every EVM chain.
///         A receipt is issued by MIZAN only when `subject` passes the check (a PASS credential in good standing),
///         and lasts 24 hours. Get one: GET https://studio.mizan.market/api/staple/<address>  (field eip712[].)
///         The domain is chain-agnostic on purpose: a receipt states a fact about an identity, it authorises nothing.
/// @dev    Published signer: https://studio.mizan.market/.well-known/mizan-keys.json (use "eip712-receipt").
///         Key rotation: a new library version adds the new signer; receipts from a retired signer stop being
///         issued and expire within 24 hours.
library MizanProof {
    struct Receipt {
        address subject;     // the address being paid, allocated to, or let in
        bytes32 credential;  // keccak256(utf8(MIZAN credential id))
        uint64 issuedAt;     // unix seconds
        uint64 expiresAt;    // unix seconds (issuedAt + 24 h)
    }

    /// @notice MIZAN's EIP-712 receipt signer. Signs receipts only; holds no funds.
    address internal constant SIGNER = 0xA958c0569c9b812AAaeD104246A806d38BcE1A26;

    bytes32 internal constant DOMAIN_TYPEHASH = keccak256("EIP712Domain(string name,string version)");
    bytes32 internal constant RECEIPT_TYPEHASH =
        keccak256("Receipt(address subject,bytes32 credential,uint64 issuedAt,uint64 expiresAt)");
    uint256 internal constant CLOCK_SKEW = 300; // tolerate a receipt issued up to 5 minutes "in the future"
    uint256 private constant HALF_N = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0;

    function domainSeparator() internal pure returns (bytes32) {
        return keccak256(abi.encode(DOMAIN_TYPEHASH, keccak256("MIZAN"), keccak256("1")));
    }

    function digest(Receipt memory r) internal pure returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(RECEIPT_TYPEHASH, r.subject, r.credential, r.issuedAt, r.expiresAt));
        return keccak256(abi.encodePacked("\x19\x01", domainSeparator(), structHash));
    }

    /// @notice Signer of a receipt, or address(0) for any malformed or malleable signature.
    function recover(Receipt memory r, bytes memory sig) internal pure returns (address) {
        return recoverDigest(digest(r), sig);
    }

    /// @notice Signer of any MIZAN EIP-712 digest; address(0) for malformed, malleable or zero signatures.
    function recoverDigest(bytes32 d, bytes memory sig) internal pure returns (address) {
        if (sig.length != 65) return address(0);
        bytes32 rr;
        bytes32 ss;
        uint8 v;
        assembly {
            rr := mload(add(sig, 32))
            ss := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return address(0);
        if (uint256(ss) > HALF_N) return address(0);
        return ecrecover(d, v, rr, ss);
    }

    /// @notice True when `r` is a live receipt, for exactly `subject`, signed by `signer`.
    function isProvenBy(address signer, address subject, Receipt memory r, bytes memory sig) internal view returns (bool) {
        if (subject == address(0) || r.subject != subject) return false;
        if (block.timestamp > r.expiresAt) return false;
        if (r.issuedAt > block.timestamp + CLOCK_SKEW) return false;
        address got = recover(r, sig);
        return got != address(0) && got == signer;
    }

    /// @notice True when `subject` holds a live MIZAN receipt. The one call most contracts need.
    function isProven(address subject, Receipt memory r, bytes memory sig) internal view returns (bool) {
        return isProvenBy(SIGNER, subject, r, sig);
    }
    // ============================================================ v2: a receipt that a subject MEETS a named requirement
    /// @notice Issued by MIZAN only when `subject` meets every clause of the requirement whose hash is `requirement`.
    struct ReceiptV2 {
        address subject;
        bytes32 credential;   // sha256(utf8(credential id)), zero if none
        bytes32 profile;      // sha256(utf8("profile@version")) of the primary claim profile
        uint8 rung;           // 0 none, 1 declared, 2 recorded, 3 proven (lowest across the requirement's clauses)
        uint8 provenance;     // bitmask: 1 market, 2 on-chain, 4 signed, 8 zkTLS, 16 TEE, 32 probe, 64 proof of control
        bytes32 requirement;  // sha256 of the requirement's canonical JSON (its published hash)
        bool met;
        uint64 issuedAt;
        uint64 expiresAt;
    }

    bytes32 internal constant RECEIPT_V2_TYPEHASH = keccak256(
        "ReceiptV2(address subject,bytes32 credential,bytes32 profile,uint8 rung,uint8 provenance,bytes32 requirement,bool met,uint64 issuedAt,uint64 expiresAt)");

    function domainSeparatorV2() internal pure returns (bytes32) {
        return keccak256(abi.encode(DOMAIN_TYPEHASH, keccak256("MIZAN"), keccak256("2")));
    }

    function digestV2(ReceiptV2 memory r) internal pure returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(RECEIPT_V2_TYPEHASH, r.subject, r.credential, r.profile, r.rung, r.provenance,
                                                  r.requirement, r.met, r.issuedAt, r.expiresAt));
        return keccak256(abi.encodePacked("\x19\x01", domainSeparatorV2(), structHash));
    }

    /// @notice True when `r` is a live receipt, signed by `signer`, that `subject` meets exactly `requirementHash` at rung >= minRung.
    function meetsBy(address signer, address subject, bytes32 requirementHash, uint8 minRung, ReceiptV2 memory r, bytes memory sig)
        internal view returns (bool)
    {
        if (subject == address(0) || r.subject != subject) return false;
        if (!r.met || r.requirement != requirementHash || r.rung < minRung) return false;
        if (block.timestamp > r.expiresAt || r.issuedAt > block.timestamp + CLOCK_SKEW) return false;
        address got = recoverDigest(digestV2(r), sig);
        return got != address(0) && got == signer;
    }

    /// @notice True when `subject` meets the requirement `requirementHash`, per a live MIZAN receipt.
    function meets(address subject, bytes32 requirementHash, uint8 minRung, ReceiptV2 memory r, bytes memory sig) internal view returns (bool) {
        return meetsBy(SIGNER, subject, requirementHash, minRung, r, sig);
    }

    // ============================================================ v3: the same, and WHO the subject acts for
    /// @notice A v2 receipt that also names the principal the subject acts for (a company domain, a key, a wallet), proven by
    /// that principal's own signature on an authority MIZAN logged. principal = sha256(utf8("dns:example.com")).
    struct ReceiptV3 {
        address subject;
        bytes32 credential;
        bytes32 profile;
        uint8 rung;
        uint8 provenance;
        bytes32 requirement;
        bool met;
        bytes32 principal;    // sha256(utf8(principal)), zero if none
        bytes32 authority;    // sha256 of the principal-signed authority (its logged hash)
        uint64 issuedAt;
        uint64 expiresAt;
    }

    bytes32 internal constant RECEIPT_V3_TYPEHASH = keccak256(
        "ReceiptV3(address subject,bytes32 credential,bytes32 profile,uint8 rung,uint8 provenance,bytes32 requirement,bool met,bytes32 principal,bytes32 authority,uint64 issuedAt,uint64 expiresAt)");

    function domainSeparatorV3() internal pure returns (bytes32) {
        return keccak256(abi.encode(DOMAIN_TYPEHASH, keccak256("MIZAN"), keccak256("3")));
    }

    function digestV3(ReceiptV3 memory r) internal pure returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(RECEIPT_V3_TYPEHASH, r.subject, r.credential, r.profile, r.rung, r.provenance,
                                                  r.requirement, r.met, r.principal, r.authority, r.issuedAt, r.expiresAt));
        return keccak256(abi.encodePacked("\x19\x01", domainSeparatorV3(), structHash));
    }

    /// @notice True when `subject` meets `requirementHash` at rung >= minRung AND acts for `principalHash`, per a live receipt by `signer`.
    function meetsWithAuthorityBy(address signer, address subject, bytes32 requirementHash, uint8 minRung, bytes32 principalHash,
                                  ReceiptV3 memory r, bytes memory sig) internal view returns (bool)
    {
        if (subject == address(0) || r.subject != subject) return false;
        if (!r.met || r.requirement != requirementHash || r.rung < minRung) return false;
        if (principalHash == bytes32(0) || r.principal != principalHash || r.authority == bytes32(0)) return false;
        if (block.timestamp > r.expiresAt || r.issuedAt > block.timestamp + CLOCK_SKEW) return false;
        address got = recoverDigest(digestV3(r), sig);
        return got != address(0) && got == signer;
    }

    function meetsWithAuthority(address subject, bytes32 requirementHash, uint8 minRung, bytes32 principalHash, ReceiptV3 memory r, bytes memory sig)
        internal view returns (bool)
    {
        return meetsWithAuthorityBy(SIGNER, subject, requirementHash, minRung, principalHash, r, sig);
    }
}


error NotProven(address subject);
error DoesNotMeet(address subject, bytes32 requirement);

/// @notice Inherit and add `onlyProven(who, receipt, signature)` to any function that moves capital.
abstract contract MizanGated {
    modifier onlyProven(address who, MizanProof.Receipt memory receipt, bytes memory signature) {
        if (!MizanProof.isProven(who, receipt, signature)) revert NotProven(who);
        _;
    }

    /// @notice Add `onlyMeets(who, requirementHash, minRung, receipt, signature)`: your own published bar, enforced on-chain.
    modifier onlyMeets(address who, bytes32 requirementHash, uint8 minRung, MizanProof.ReceiptV2 memory receipt, bytes memory signature) {
        if (!MizanProof.meets(who, requirementHash, minRung, receipt, signature)) revert DoesNotMeet(who, requirementHash);
        _;
    }
}
