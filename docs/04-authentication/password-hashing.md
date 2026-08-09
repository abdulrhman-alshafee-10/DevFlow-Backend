# Password Hashing

## 1. What Is It?

Password hashing is the process of converting a plain-text password into an irreversible string (hash) using a one-way cryptographic function. The hash is stored in the database instead of the password. During login, the submitted password is hashed and compared to the stored hash.

---

## 2. Why Does It Matter?

If your database is compromised (and databases do get compromised), password hashing means:
- Attackers cannot read users' passwords
- Users who reuse passwords on other sites are protected
- Even with the hash, cracking modern password hashes is computationally infeasible

Without hashing, a single database breach exposes every user's password in plain text.

---

## 3. When Should I Use It?

- **Always** — Every password stored in a database must be hashed
- **Password creation** — During registration
- **Password change** — When users update their password
- **Password reset** — When setting a new password

---

## 4. When Should I NOT Use It?

- **Tokens** — JWTs and refresh tokens are signed, not hashed (though refresh tokens can be hashed in the DB)
- **API keys** — These should be hashed in the DB (treated like passwords)
- **Reversible encryption** — When you need to decrypt the data later (e.g., encrypted user data), use encryption, not hashing

---

## 5. How Does It Work?

### Why Not SHA-256?

General-purpose hash functions (SHA-256, MD5) are too fast. An attacker with a GPU can compute billions of SHA-256 hashes per second, making brute-force attacks feasible.

### Password Hashing Functions

**bcrypt** (recommended for DevFlow):
- Deliberately slow (configurable cost factor)
- Built-in salt (random data mixed in)
- Widely used, battle-tested
- Cost factor of 12 means ~250ms per hash (too slow for brute-force, fine for login)

**argon2** (alternative):
- Newer, winner of the Password Hashing Competition
- Configurable memory, time, and parallelism
- Harder to accelerate with GPUs
- Less widely supported (but growing)

### How bcrypt Works

```
Input: "MyP@ssw0rd"
    ↓
Generate random salt: "$2b$12$LJ3m4..."
    ↓
Hash(password + salt, cost_factor=12)
    ↓
Output: "$2b$12$LJ3m4...hashed_result"
        ↑      ↑     ↑
     algorithm cost  salt + hash (60 chars)
```

The salt is stored as part of the hash, so you don't need a separate salt column.

### Verification

```
Stored hash:  "$2b$12$LJ3m4...hashed_result"
User input:   "MyP@ssw0rd"
    ↓
Extract salt from stored hash
Hash(input + salt, cost_factor=12)
Compare result with stored hash
    ↓
Match? → Authenticated
No match? → Invalid credentials
```

---

## 6. How Does It Fit Into DevFlow?

- **Registration** — Hash the password before storing the user
- **Login** — Verify the submitted password against the stored hash
- **Password change** — Verify old password, hash new password
- **Password reset** — Hash the new password after verifying the reset token
- **Refresh token storage** — Hash refresh tokens before storing in DB

Use `passlib` with the bcrypt backend for all password operations.

---

## 7. Common Mistakes

### Using MD5 or SHA-256

These are NOT password hashing functions. They're fast hash functions designed for integrity checks, not security.

### Low Cost Factor

A cost factor of 4 is too fast. Use 12+ for bcrypt. Test that verification takes 200-400ms.

### Implementing Your Own Hashing

Never write your own password hashing. Use `passlib[bcrypt]` or `argon2-cffi`.

### Logging Passwords

Never log plain-text passwords, even in debug mode. Log "login attempt for user@email.com", not the password.

### Not Upgrading Hash Cost Over Time

Hardware gets faster. What's secure today might be crackable in 5 years. Check and upgrade cost factor on login.

---

## 8. Production Considerations

- **Cost factor tuning** — Set the cost factor so hashing takes 200-400ms on your production hardware
- **Timing attacks** — Use constant-time comparison to prevent timing-based password guessing
- **Password policies** — Enforce minimum length (12+), but don't require complex rules (they lead to weaker passwords)
- **Breached password checking** — Check passwords against known breached lists (Have I Been Pwned API)
- **Hash migration** — If upgrading from SHA-256 to bcrypt, rehash on next login

---

## 9. Prerequisites

- Basic cryptography concepts (hashing vs. encryption)
- Understanding of why password storage matters

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain why bcrypt is used instead of SHA-256
- [ ] Hash passwords with passlib/bcrypt
- [ ] Verify passwords against stored hashes
- [ ] Choose an appropriate cost factor
- [ ] Understand salting and why it's necessary
- [ ] Explain the difference between hashing and encryption
