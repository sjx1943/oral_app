# Development Log

## 2025-09-22

*   **Project Initialization & Planning:**
    *   Finalized the SROP (Scalable Real-time Oral Practice) architecture as the core design.
    *   Established a detailed, four-phase development plan in `docs/TODO.md`.
    *   Added a critical task for a "Prompt Management Module" to ensure personalized AI interaction.
*   **Foundation & Data Persistence:**
    *   Set up the local development environment using Docker.
    *   Created a `docker-compose.yml` to manage PostgreSQL, MongoDB, and Redis services.
    *   Successfully launched the required database and cache containers.
    *   Defined the initial PostgreSQL database schema for the `user-service`, including support for third-party authentication (e.g., Google, Apple) and user-specific attributes like `native_language`.

## 2025-09-23

*   **User Service Implementation & Debugging:**
    *   Completed the initial implementation of the `user-service` with registration and login logic.
    *   Containerized the service using a `Dockerfile`.
*   **Intensive Docker Environment Troubleshooting:**
    *   Diagnosed and resolved a persistent `Cannot find module 'dotenv'` error, which was caused by a corrupted local Docker cache that ignored `--no-cache` flags. The issue was bypassed by using a direct `docker build --no-cache` command.
    *   Solved the subsequent `relation "users" does not exist` error by creating an `init.sql` script and configuring the `postgres` container to run it on startup.
    *   Fixed a `password authentication failed` error by correcting a credentials mismatch between the `user-service`'s `.env` file and the `docker-compose.yml` configuration.
    *   Resolved the final issue where configuration changes were not being applied on `docker compose restart` by performing a full `down` and `up` cycle to force a complete container recreation.
*   **Success & Verification:**
    *   Successfully registered a new user via the `/api/users/register` endpoint, confirming the end-to-end functionality of the service.
    *   Verified the user data was correctly written to the `users` and `user_identities` tables in the PostgreSQL database.
*   **Planning & Documentation:**
    *   Updated the project `TODO.md` to mark the user service implementation as complete.
    *   Added new backlog tasks for comprehensive API endpoint testing and for updating the `schema.md` documentation to match the current database structure.

## 2025-09-29

*   **Architecture Upgrade:**
    *   Redesigned the AI Engine's architecture to support a flexible, hybrid model. The system can now accommodate both the traditional, pipelined approach (ASR -> LLM -> TTS) and a unified, end-to-end multimodal model (e.g., Qwen3-Omni).
    *   Updated `GEMINI.md` and `docs/TODO.md` to reflect this key architectural decision.
*   **API Gateway Implementation:**
    *   Successfully implemented and containerized an API Gateway using Nginx.
    *   Configured the gateway to route all incoming traffic from `/api/users` to the `user-service`.
*   **Troubleshooting & Verification:**
    *   Resolved a host port conflict by remapping the gateway's external port from `80` to `8080`.
    *   Fine-tuned Nginx `location` and `proxy_pass` directives to ensure correct URL path rewriting.
    *   Verified the end-to-end request flow (`curl -> api-gateway -> user-service`) is fully functional.
*   **Project Management:**
    *   Marked the API Gateway setup task as complete in the project's `TODO.md`.
