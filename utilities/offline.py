import minecraft_launcher_lib
import subprocess
import os

# Cartella Minecraft (modificabile)
minecraft_dir = os.path.join(os.path.expanduser("~"), "Downloads", "RedModpacksMinecraft")
os.makedirs(minecraft_dir, exist_ok=True)

options = minecraft_launcher_lib.utils.generate_test_options()

def cc_usrname(usrname:str):
    # Account di test offline
    options['username'] = usrname
    print(f"Username offline: " + options['username'])

def launch(scelta:str):
    if scelta == "1":
        version_id = "1.21.8"
        print("Installazione Fabric 1.21.8...")
        minecraft_launcher_lib.fabric.install_fabric(version_id, minecraft_dir)
        # Lancia il gioco
        cmd = minecraft_launcher_lib.command.get_minecraft_command(f"{version_id}", minecraft_dir, options)
    elif scelta == "2":
        version_id = "1.21.1"
        print("Installazione Forge 1.21.1...")
        forge_version = minecraft_launcher_lib.forge.find_forge_version(version_id)
        if forge_version is None:
            print("Non è stata trovata una versione Forge compatibile!")
            exit()
        minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_dir)
        # Lancia il gioco
        cmd = minecraft_launcher_lib.command.get_minecraft_command(forge_version, minecraft_dir, options)
    else:
        print("Scelta non valida!")
        exit()

    # Avvio offline di Minecraft
    print("Avvio Minecraft...")
    subprocess.run(cmd)
