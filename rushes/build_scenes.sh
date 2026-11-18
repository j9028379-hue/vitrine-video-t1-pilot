#!/usr/bin/env bash
# Reconstruit les quatre prises vidéo de démonstration (6 / 8 / 7 / 9 s) à partir
# de rushs Mixkit sous licence libre d'usage commercial (Mixkit Stock Video Free License).
#
#   bash rushes/build_scenes.sh
#
# Les originaux Mixkit ne sont pas versionnés dans ce dépôt : ils sont téléchargés
# ici, vérifiés par SHA-256 (voir rushes/manifest.json → raw_sources), puis assemblés.
# Aucune photographie fixe n'est utilisée : les quatre prises sont des vidéos animées.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
D="$ROOT/rushes/source/demo_v4"
mkdir -p "$D"
FIT="scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=30"

fetch() { # id filename
  local id="$1" out="$D/$2"
  if [ ! -f "$out" ]; then
    curl --fail --location --silent --show-error --retry 3 --max-time 180 \
      --user-agent "Mozilla/5.0" --referer "https://mixkit.co/free-stock-video/" \
      "https://assets.mixkit.co/videos/$id/$id-720.mp4" --output "$out"
  fi
  echo "ok $out"
}

cut() { # src start dur out
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$D/$1" -vf "$FIT" -an \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$D/$4"
}

echo "— Téléchargement et vérification des rushs sources"
fetch 327   327.mp4
fetch 48322 48322.mp4
fetch 3533  3533.mp4
fetch 29059 29059.mp4
fetch 2597  2597.mp4
fetch 41222 41222.mp4
python3 "$ROOT/engine/verify_raw_rushes.py"

echo "— Prise 1 (6 s) : le serveur pose l'assiette, main qui sert"
cut 327.mp4 0.30 6.0 S1.mp4

echo "— Prise 2 (8 s) : le plat vu d'au-dessus, puis détail très proche"
cut 48322.mp4 1.0 4.0 s2a.mp4
cut 3533.mp4  1.0 4.0 s2b.mp4
printf "file 's2a.mp4'\nfile 's2b.mp4'\n" > "$D/s2list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$D/s2list.txt" -c copy "$D/S2.mp4"

echo "— Prise 3 (7 s) : la personne qui mange, visage et sourire"
cut 29059.mp4 3.0 7.0 S3.mp4

echo "— Prise 4 (9 s) : l'entrée et la terrasse vues depuis la rue, puis le comptoir"
cut 2597.mp4  0.4 4.6 s4a.mp4
cut 41222.mp4 0.5 4.4 s4b.mp4
printf "file 's4a.mp4'\nfile 's4b.mp4'\n" > "$D/s4list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$D/s4list.txt" -c copy "$D/S4.mp4"

echo "— Durées obtenues (attendu 6 / 8 / 7 / 9 s)"
for s in S1 S2 S3 S4; do
  printf "%s %s\n" "$s" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$D/$s.mp4")"
done
echo "Terminé. Rendu : python3 engine/motion_v3_1.py --plan render_plan_v4_demo.json --output output/output_T1_sans_voix_v4_demo.mp4"
