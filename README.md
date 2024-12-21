# Elaway Gateway API

Elaway Charge API is a Node.js application that interacts with the Elaway charging infrastructure. It provides an interface to manage and monitor electric vehicle (EV) charging points using the Elaway API.

## Features

- Authenticate with the Elaway API using OAuth2.
- Retrieve and manage charging point data.
- Start and stop charging sessions.
- TODO: Automatically refresh access tokens to maintain session validity.

## Prerequisites

- Node.js
- Docker (optional, for containerized deployment)

## Installation

The recommended way would be to use docker. Copy the docker-compose.yml.example and fill in your information.

For legal reasons the client secrets are not provided here, but can be aquired with [mitmproxy](https://www.google.com/search?q=mitmporxy).
