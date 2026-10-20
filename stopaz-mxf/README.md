# Stopáž MXF

Malý pomocník, který ve vybrané složce zjistí stopáž všech MXF souborů a vypíše je seřazené od nejdelšího.

## Co dělá

- Pomocí `ffprobe` zjistí délku a snímkovou frekvenci každého souboru.
- Délku převede na televizní formát `MM:SS:FF` (minuty, sekundy, framy).
- Přeskočí soubory se stopáží přesně 25:00 a soubory, které nejdou přečíst.
- Výsledek uloží do `stopaze.txt` ve stejné složce.

## Spuštění

Potřebuješ Python 3.7 nebo novější a [FFmpeg](https://ffmpeg.org/) (`ffprobe`) v systémové cestě. Žádné další knihovny nejsou potřeba.

```
python stopaz_mxf.py
```

## O vzniku

Vytvořeno s pomocí AI (Claude).
