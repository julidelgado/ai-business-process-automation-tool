Copy-Item -Path ".env.example" -Destination ".env" -ErrorAction SilentlyContinue

docker compose up --build
