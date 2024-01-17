# LATTICE: Collective Observation to AI-Assisted Action

![Group wearing headgear sharing perception](docs/group.webp)

---

### WHAT WE ARE BUILDING

The central goal of this project is to create multiple devices for video, audio, and sensory streaming, enabling an AI system to help coordinate an individual or collective towards a goal in realtime. This initial version requires each person to wear a [HALO](device/halo) for continuous streaming and feedback from the system.

This system began development within our community of [self-taught synthetic biologists](https://undergroundgarden.club) engineering plants to secrete insulin and exploring climate biotech ideas. By streaming thoughts, observations, and hardware sensors, we are seeding an AI system to train new members and coordinate existing members rotating on wet lab work in between their day/night jobs. AI is our bridge. Bi-directional conversation is the medium.

![Diagram of passive/active AI observations](docs/collectivebridges.png)

### EXPLORATORY DEVELOPMENT

| 🟩 | STAGE | DESCRIPTION | EX |
| --- | --- | --- | --- |
| 🟩 | ALPHA1 | Wearable device sensor data ingestion (i.e., HALO) and passive multi-modal knowledge distillation. Callable AI tools | |
| 🟦 | ALPHA2 | Passive Observer AI agent + Multi-Stream | |
| ⬜️ | ALPHA3 | Plugins system for AI actions to external services | |
| ⬜️ | ALPHA4 | Sensor data ingestion (i.e., lab equipment, orb) | |
| ⬜️ | ALPHA5 | Truffle Brain integration. Control the Weights |

### HARDWARE / WEARABLES TEMPLATES

- [**HALO**](/device/halo): Headgear for video/audio/??? observation streaming and bi-directional AI interactions
- **ORB**: [TODO] Static device for video/audio/??? input of a broad area and/or group

---

### GETTING STARTED

##### SYSTEM DESIGN

There are two primary pieces to this tool at the moment:

> **Hardware**: Build and setup instructions are in the `/devices` directory. We're using Raspberry Pis to simplify using this tool and ensuring good video/audio processing. Once interaction patterns are sturdy, we'll create our regalpunk aesthetic head piece and hardware configuration.

> **AI Agents**: Backend parses multimedia queries from devices, determines actions to take (starting queries in `actor_tools.py`), and passes it to a respective tool/process. Passive AI agent activity will be worked on next.

We want to push exploration of interactivity on devices and the edge. Viewing the data directly and/or in a web UI is an anti-pattern and a sign that our edge hardware patterns are failing. At most, we may create it to provide permalinks to artifacts created by AI agents.

##### RUNNING LOCALLY

Right now, we're just concerned with running locally, and using `ngrok` to push data from devices to our backend. Dockerized services should make it easy for you to run with a cloud provider if you like. As for running locally:

- Create an `.env` file in the root directory for docker compose. This requires a few services which you will see in the backend `env.py`
- Build/setup your [HALO](/device/halo/) hardware device (instructions in [sub-directory](/device/halo/))
- Start a `ngrok` tunnel pointing at the local API for your device to send data through (to be improved/changed) Ex cmd I run: `ngrok http 3000 --domain yourprefixhere.ngrok.app --scheme=http`
- Ensure your hardware device's API url env param is pointing at that ngrok tunnel endpoint (may require forcing to `http` at the moment)
- `bash manage.sh local setup` to do installs for things you'll need
- `docker-compose up` the API/Worker/Queue/PGVector DB
- `bash manage.sh local migrate-app head` to get your postgres db updated
- Triple click to begin your (((HALO))) observer!
- Build collective knowledge, informing future actions you and your collective will take.

---

### CONTRIBUTING

Open up some discssions, issues, and PRs about your wild ideas. We want to use Github discussions to ensure knowledge can be found by new folks setting up their systems. In the not so distant future, we can build a lattice system for contributors to work together through.

