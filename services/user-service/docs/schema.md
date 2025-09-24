# User Service Database Schema

This document defines the PostgreSQL schema for the User Service.

## Table: `users`

Stores core user profile information, independent of the authentication method.

| Column          | Type             | Constraints              | Description                                  |
|-----------------|------------------|--------------------------|----------------------------------------------|
| `id`            | `UUID`           | `PRIMARY KEY`            | Unique identifier for the user.              |
| `username`      | `VARCHAR(50)`    | `UNIQUE`, `NOT NULL`     | User's chosen display name.                  |
| `email`         | `VARCHAR(255)`   | `UNIQUE`                 | User's email address (optional, can be null).|
| `avatar_url`    | `TEXT`           |                          | URL for the user's profile picture.          |
| `native_language` | `VARCHAR(10)`  |                          | User's native language (e.g., 'en-US').      |
| `learning_goal` | `TEXT`           |                          | User's stated language learning objectives.  |
| `created_at`    | `TIMESTAMPTZ`    | `NOT NULL`, `DEFAULT NOW()` | Timestamp of user creation.                  |
| `updated_at`    | `TIMESTAMPTZ`    | `NOT NULL`, `DEFAULT NOW()` | Timestamp of last user profile update.       |

## Table: `user_identities`

Links third-party authentication providers to a user account. A single user can have multiple identities.

| Column         | Type           | Constraints                               | Description                                       |
|----------------|----------------|-------------------------------------------|---------------------------------------------------|
| `provider`     | `VARCHAR(50)`  | `PRIMARY KEY`                             | Name of the auth provider (e.g., 'google', 'apple'). |
| `provider_uid` | `VARCHAR(255)` | `PRIMARY KEY`                             | The user's unique ID from the provider.           |
| `user_id`      | `UUID`         | `FOREIGN KEY` (references `users.id`) | Links to the corresponding user in the `users` table. |
| `created_at`   | `TIMESTAMPTZ`  | `NOT NULL`, `DEFAULT NOW()`               | Timestamp of identity creation.                   |

---
*This design allows a user to sign up with Google and later link their Apple account, all pointing to the same central user profile.*
