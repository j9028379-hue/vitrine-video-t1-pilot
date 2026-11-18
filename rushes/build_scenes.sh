#!/usr/bin/env bash
# Reconstruit les quatre prises vidéo de démonstration (6 / 8 / 7 / 9 s) à partir
# de rushs Mixkit sous licence libre d'usage commercial (Mixkit Stock Video Free License).
#
#   bash rushes/build_scenes.sh
#
# Nouveautés de la clôture T1 :
#  * les prises sont assemblées au plus près de la définition native du rush (variante 1080
#    quand elle existe, 720 sinon), au lieu d'un 720×1280 forcé ;
#  * aucun agrandissement n'est subi à la construction : le recadrage 9:16 se fait directement
#    dans les pixels du rush. La mise à l'échelle finale 9:16 → 720×1280 est faite une seule
#    fois, par le moteur, après le recadrage du plan (voir engine/motion_v4.py).
#
# Aucune photographie fixe n'est utilisée : les quatre prises sont des vidéos animées.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
D="$ROOT/rushes/source/demo_v4"
mkdir -p "$D"

fetch() { # id fichier_local
  local id="$1" out="$D/$2"
  if [ ! -f "$out" ]; then
    case "$2" in
      *-1080.mp4) url="https://assets.mixkit.co/videos/$id/$id-1080.mp4" ;;
      *)          url="https://assets.mixkit.co/videos/$id/$id-720.mp4" ;;
    esac
    curl --fail --location --silent --show-error --retry 3 --max-time 240 \
      --user-agent "Mozilla/5.0" --referer "https://mixkit.co/free-stock-video/" \
      "$url" --output "$out"
  fi
  echo "ok $out"
}

cut() { # src début durée sortie largeur hauteur
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$D/$1" \
    -vf "crop=ih*9/16:ih,scale=$5:$6,setsar=1,fps=30" -an \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$D/$4"
}

concat() { # a b liste sortie
  printf "file '%s'\nfile '%s'\n" "$1" "$2" > "$D/$3"
  ffmpeg -v error -y -f concat -safe 0 -i "$D/$3" -c copy "$D/$4"
}

echo "— Téléchargement et vérification des rushs sources (variante la plus définie disponible)"
fetch 327   327-1080.mp4
fetch 48322 48322.mp4
fetch 3533  3533-1080.mp4
fetch 29059 29059.mp4
fetch 2597  2597-1080.mp4
fetch 41222 41222-1080.mp4
python3 "$ROOT/engine/verify_raw_rushes.py"

echo "— Prise 1 (6 s, 606×1080) : le serveur pose l'assiette, main qui sert"
cut 327-1080.mp4 0.30 6.0 S1.mp4 606 1080

echo "— Prise 2 (8 s, 606×1080) : le plat vu d'au-dessus, puis détail très proche"
cut 48322.mp4     1.0 4.0 s2a.mp4 606 1080
cut 3533-1080.mp4 1.0 4.0 s2b.mp4 606 1080
concat s2a.mp4 s2b.mp4 s2list.txt S2.mp4

echo "— Prise 3 (7 s, 404×720) : la personne qui mange, visage et sourire"
cut 29059.mp4 3.0 7.0 S3.mp4 404 720

echo "— Prise 4 (9 s, 606×1080) : l'entrée et la terrasse vues depuis la rue, puis le comptoir"
cut 2597-1080.mp4  0.4 4.6 s4a.mp4 606 1080
cut 41222-1080.mp4 0.5 4.4 s4b.mp4 606 1080
concat s4a.mp4 s4b.mp4 s4list.txt S4.mp4

echo "— Définition et durées obtenues (attendu 6 / 8 / 7 / 9 s)"
python3 - <<PY
import cv2, pathlib
for s in ("S1", "S2", "S3", "S4"):
    p = pathlib.Path("$D") / f"{s}.mp4"
    c = cv2.VideoCapture(str(p))
    n = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); w = int(c.get(3)); h = int(c.get(4))
    print(f"{s}: {w}x{h} — {n} images — {n/30:.2f} s")
    c.release()
PY
echo "Terminé. Rendu : PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \\"
echo "          --output output/output_T1_master_final.mp4 --manifest reports/execution_manifest_v4.json"
