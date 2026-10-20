# Whisper – kontrola upoutávek

Hromadná kontrola televizních upoutávek pomocí rozpoznávání řeči (OpenAI Whisper).

Upoutávka na konci říká, kdy pořad běží („v úterý ve 20:05 na TV Barrandov“). Když se na to při výrobě spletlo, šla do vysílání chybná informace. Ruční poslech desítek upoutávek denně je zdlouhavý, tak to dělá tento skript.

## Co dělá

1. Ve vybrané složce najde všechna videa (MOV, MXF, MP4, AVI, MKV).
2. Z každého vytáhne posledních 15 sekund zvuku a filtrem zvýrazní řeč a potlačí hudbu (FFmpeg).
3. Řeč přepíše do textu modelem Whisper `medium` v češtině.
4. Z názvu souboru vyčte očekávaný den a čas (například `..._utery_2005.mxf` znamená úterý 20:05).
5. Porovná je s přepisem. Pozná čísla i slovní tvary („dvacet nula pět“, „ve středu“).
6. Výsledek průběžně zapisuje do `prepisy_vsech_upoutavek.txt` s označením ✅ sedí nebo ❌ nesedí.

## Spuštění

Potřebuješ Python 3.7 nebo novější a [FFmpeg](https://ffmpeg.org/) v systémové cestě.

```
pip install -r requirements.txt
python kontrola_upoutavek.py
```

Po spuštění vybereš složku s upoutávkami. Model `medium` se při prvním spuštění stáhne (asi 1,5 GB).

## O vzniku

Vytvořeno s pomocí AI (Claude). Zadání, testování na reálném materiálu a ladění jsou moje.
