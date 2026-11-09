---
theme: main
title: Encryption Basics (Model Example)
---

# Encryption Basics

<!-- Model deck: every question format the extractor supports. See slide_extraction.md. -->

---

<!-- _class: numbered -->

## How an encrypted message travels

1. Write the message
2. Encrypt it with a key
3. Send it over the network
4. Decrypt it with a key

---

## In symmetric encryption, which key decrypts the message?

1. The same key that encrypted it
2. A different key from the one that encrypted it
3. No key is needed to decrypt it
4. Any key of the same length

<!-- question
answer: A
-->

---

## Spot the lie!

1. Encryption can be reversed with the right key.
2. Encrypted data looks random without the key.
3. A longer key always makes a message shorter.

<!-- question
ask: Which statement about encryption is false?
answer: C
-->

---

## Spot the lie!

1. In asymmetric encryption, the public key can be shared with anyone.
2. In asymmetric encryption, the private key should be shared with friends.
3. Asymmetric encryption uses two different keys.

<!-- Ask for a show of hands before revealing the answer. -->

<!-- question
ask: Which statement about asymmetric encryption is false?
answer: B
-->

---

Talk with your partner, then choose one.

1. Bob's public key
2. Bob's private key

<!-- question
ask: Alice wants to send Bob a secret message. Which key should she encrypt it with?
answer: A
-->

---

## Where do you already use encryption?

1. Messaging apps
2. Online banking
3. Websites that use HTTPS

---

## Why can't Alice just send the key along with the message?

<!-- question
answer: Anyone who intercepts the message also gets the key, so they can decrypt it.
  The key needs a separate, safe way to reach Bob.
-->

---

<!-- _class: numbered -->

## Your school wants to protect student records. What would you recommend?

Think about:

1. Who needs access
2. Where the keys are kept
3. What happens if a key is lost

<!-- question
answer: Encrypt the records, and give keys only to staff who need them. Store keys apart from
  the data, and keep a secure backup so a lost key doesn't mean lost records.
-->

---

## What does a question slide look like in Markdown?

This code block is only an example, so it isn't a question:

```markdown
<!-- question
answer: A
-->
```

---

## Exit ticket: which key decrypts it?

1. The same key that encrypted it
2. A different key from the one that encrypted it
3. No key is needed to decrypt it
4. Any key of the same length

<!-- question
ask: In symmetric encryption, which key decrypts the message?
answer: A
-->

---

## Which of these can safely be shared with anyone?

1. A public key
2. A private key
3. An encrypted message
4. A symmetric key

<!-- question
answer: A
answer: C
-->

---

## How could Alice get a symmetric key to Bob safely?

<!-- question
answer: Hand it to Bob in person, so it never crosses the network.
answer: Encrypt it with Bob's public key, so only Bob's private key can recover it.
-->

---

<!-- _class: wrong-answer -->

## What does a private key do?

Only submit *creative wrong answers* that your classmates might pick!

<!-- question
answer: It decrypts messages that were encrypted with the matching public key.
answer:
-->

---

<!-- _class: best-answer -->

## What does a private key do?

Now write the best *correct answer* that you can.

<!-- question
answer: It decrypts messages that were encrypted with the matching public key.
-->
