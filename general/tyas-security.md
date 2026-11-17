Based on my observations of the past year, listed below are the things that I think would be great to improve at TYAS.

Please note that this is not comprehensive, I have a more detailed security report if you need the technical details but these are the most practical to solve at the moment.

# Threat Model (likely to happen with some impact)

1. Sharing a Google sheet with student data (accidentally or intentionally).
2. Someone getting access to a Gradelink admin.
3. Someone getting access to a Google Workspace admin.
4. Someone getting access to a teacher account (google workspace or gradelink).
5. AI models get trained on student data or accessed through a hacked ChatGPT/Claude account.

# Possible Mitigations (how we can prevent or mitigate damage)

## Most important Idea: Least Privilege Access

1. TYAS Portal will be the backup and be the access controlled version of our student data (along with Gradelink) - this is what apps created by office staff will rely on so that data can be easily traced and revoked as needed. This is how teachers will also get bulk student data.
2. As much as possible, keep data off Google Sheets or at the very least only have one copy and harden that copy (@teachers @office only).
3. TYAS Portal will only be accessible from 211.x (school address), external access needs additional permission.
4. Remove Gradelink admin access to people that might not need it and harden those that use it. (2FA with hardware security key or secure TOTP).
5. Google Workspace Admins should be logically separate and protected by proper 2FA (hardware security key or secure TOTP).
6. Any data kept for app use or temporary use should be deleted as soon as possible.
7. Use of AI on data should be limited to API use or a local LLM - this prevents student or sensitive data from being used to train future AI models.
(API is credit-based AI usage. This might be more effective for us as a school than individual subscriptions to AI)
8. MFA on all staff accounts (already implemented).
9. Workspace sharing restrictions (already implemented, needs further configuration).

For the Local AI: I already have this running on the school server, I am just in the process of polishing it for speed and convenience.

For the API usage: This will be very easy to implement, I just need a decision on how much credits we will get monthly for teacher use.
