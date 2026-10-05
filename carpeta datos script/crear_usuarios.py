import csv
import secrets
import subprocess
import sys
from pathlib import Path

# useradd solo existe en Linux: en Windows (o con --dry-run) se genera el CSV
# con las contraseñas pero no se crea ningún usuario.
DRY_RUN = "--dry-run" in sys.argv or sys.platform != "linux"

# En Colab los datos viven en Drive; fuera de Colab, junto a este script.
colab_dir = Path.cwd() / "drive/MyDrive/Colab Notebooks"
cwd = colab_dir if colab_dir.exists() else Path(__file__).resolve().parent

rows = []

with open(cwd / "data/users_in.csv", "r", newline="", encoding="utf-8") as file_input, \
        open(cwd / "data/users_out.csv", "w", newline="", encoding="utf-8") as file_output:
    reader = csv.DictReader(file_input)
    # El CSV de entrada puede no traer la columna "password".
    fieldnames = list(reader.fieldnames)
    if "password" not in fieldnames:
        fieldnames.append("password")
    writer = csv.DictWriter(file_output, fieldnames=fieldnames)
    writer.writeheader()

    for user in reader:
        user["password"] = secrets.token_hex(8)
        useradd_cmd = [
            "/sbin/useradd",
            "-c", user["real_name"],
            "-m",
            "-G", "users",
            user["username"]
        ]
        if not DRY_RUN:
            subprocess.run(useradd_cmd, check=True)
            # useradd -p espera el hash, no el texto plano; chpasswd lo cifra.
            subprocess.run(
                ["/sbin/chpasswd"],
                input=f"{user['username']}:{user['password']}\n",
                text=True,
                check=True,
            )
        writer.writerow(user)
        rows.append(user)

if DRY_RUN:
    print("Simulado: no se crean usuarios (useradd solo existe en Linux).\n")

# Muestra el contenido de users_out.csv como tabla.
widths = {f: max(len(f), *(len(r[f]) for r in rows)) for f in fieldnames}
print("  ".join(f.ljust(widths[f]) for f in fieldnames))
print("  ".join("-" * widths[f] for f in fieldnames))
for r in rows:
    print("  ".join(r[f].ljust(widths[f]) for f in fieldnames))
