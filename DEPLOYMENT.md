# Docker and AWS EC2 deployment

This setup runs the app as a Docker container on one EC2 instance. SQLite,
uploaded encrypted files, and the file-encryption key live in a Docker volume,
so rebuilding or replacing the container does not replace those files. Keep
backups of the volume: losing the encryption key makes uploaded files
unreadable.

## Run locally with Docker Compose

Create a `.env` file in the project root containing a newly generated signing
secret:

```text
SECRET_KEY=replace-this-with-a-long-random-secret
```

Do not commit `.env`. Build and run:

```powershell
docker compose up --build -d
```

Open `http://localhost:8000`. Check `http://localhost:8000/health` for
`{"status":"ok"}`. Stop the app with `docker compose down`; its persistent
volume remains. To intentionally remove the stored database, encryption key,
and uploads as well, use `docker compose down --volumes`.

## Deploy on an AWS Free Tier-eligible EC2 instance

Free Tier eligibility, credits, instance types, and included hours depend on
your AWS account, its creation date, and region. Confirm the current offer in
the AWS Free Tier and Billing consoles before launching; EC2 storage, public
IPv4 addresses, data transfer, and other resources can still incur charges.
Set a billing budget/alert.

1. Create an EC2 instance using an instance type currently shown as eligible
   for your account and region. Use a supported Linux image and a small root
   EBS volume.
2. In its security group, allow SSH (port 22) only from your IP. For initial
   testing, allow TCP port 8000 only from your IP; do not expose it to all
   internet addresses.
3. Install Docker and the Docker Compose plugin using the instructions for
   the Linux image you selected, then connect to the instance.
4. Get this project onto the instance (for a private repository, configure
   repository access without putting credentials in the image).
5. In the project directory, create `.env` with a unique signing secret. For
   example, generate one on the instance with `openssl rand -hex 32` and put
   the result after `SECRET_KEY=`. Keep `.env` private and out of source
   control.
6. Start the container with `docker compose up --build -d`. Check startup
   using `docker compose ps`, `docker compose logs app`, and
   `curl http://localhost:8000/health`.
7. Visit `http://<EC2-public-address>:8000` from the IP allowed in step 2.

The named Docker volume is on the instance's EBS disk, not an independent
backup. Back it up before instance replacement or data migration. This
single-instance SQLite setup is intended for a small test/development
deployment, not a highly available or multi-instance production service.
Before public production use, add HTTPS with a domain and reverse proxy or a
load balancer, tighten access rules, and plan managed database/object storage
and backups.
