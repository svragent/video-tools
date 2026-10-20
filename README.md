# video-tools

Nástroje pro práci s videem a zvukem, které jsem postavil pro televizní provoz a sociální sítě. Píšu je v Pythonu s pomocí AI (Claude): zadání, testování na reálném materiálu a ladění jsou moje.

## Nástroje

| Nástroj | Co dělá |
|---|---|
| [Pipeline Video Generator](pipeline-upoutavky/) | Automatická výroba TV upoutávek: data z Excelu, párování videa a zvuku, titulky, export do XDCAM. 400+ hodin práce měsíčně. *(jen popis, kód není veřejný)* |
| [Reels Cropper](reels-cropper/) | Převede vodorovné video na svislé 9:16. Sám najde střihy a obličeje, rámeček jde animovat keyframy, export přes FFmpeg. |
| [Whisper – kontrola upoutávek](whisper-kontrola-upoutavek/) | Přepíše konec upoutávek pomocí AI (Whisper) a zkontroluje, že sedí den a čas vysílání. |
| [Rozpoznávání hudby](rozpoznavani-hudby/) | Najde použitou hudbu ve vysílacích MXF přes ACRCloud API a spočítá délku každé skladby. Fronta a časovač. |
| [Stopáž MXF](stopaz-mxf/) | Vypíše stopáž všech MXF ve složce ve formátu MM:SS:FF. |

## Autor

Jan Červenák – efektivita a automatizace procesů, vývoj nástrojů s pomocí AI. Deset let v Barrandov Televizní Studio (střih, správa systému Avid, vedení oddělení upoutávek).
