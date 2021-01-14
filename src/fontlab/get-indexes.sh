if [[ -z "$1" || ! -f "$1" || "$1" != *.vfj ]]
then
  echo "Argument should be a VFJ file path"
  exit 1
fi
echo $(cat $1 | jq -r '.font.glyphs | to_entries | reduce .[
] as $i ({}; .[$i.value.name] = $i.key)') > "$1.json"