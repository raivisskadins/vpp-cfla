# VPP CFLA

[Kāds ir projekta mērķis, kas tajā ir izdarīts - marķēti dati, LLM + RAG sistēma, embedding modeļu fine-tuning]

## Projekta sastāvdaļas
Projekts sastāv no 2 vidēm testa un demo.
Testa vidē ietilpst viss, izņemot demo mape, kas ir demo videi.
Informāciju par demo vides uzstādīšanu un lietošanu meklēt demo mapes README.MD

Testa vides galvenais darbināmais skripts ir "ProjectProcurementReview.ipynb"
Skriptu palaižot, tas iziet cauri visiem failiem "config" mapē (ja lietojam testa kopu), padodod LLM modelim jautājumus, uz kuriem tas sniedz atbildes, ņemot vērā nolikumu un iepirkuma līgumu, tad atgriež rezultātu tabulu un izveido .csv un .html formātu report failus, kuros ir apskatāma sīka informācija par katru jautājumu. Pēc tam tiek izveidots main_report.html, kurā var apskatīt, pārskatāmāku sarakstu ar iepirkumiem, kuru iespējams izvērst un apskatīt visus jautājumus detalizēti. Beigās izveidojas precision_report.html fails, kurā var apskatīt katra apstrādātā jautājuma precizitātes un papildus novērtēšanas datus, par apstrādes sniegumu. Tiek izveidots arī report.htm, fails, kas ir veca versija main_report.html.

"PromptTest.ipynb" iespējams notestēt individuālas uzvednes.

## Kā uzstādīt?
Sistēmas darbināšanai nepieciešama pietiekami stipra darba stacija. Iesakāms, ka lietotājam ir vismaz 16GB RAM un vēlams arī laba video karte.
Vispirms nepieciešams aizpildīt .env-example failu ar pareizajām vertībām un pārsaukt uz -> .env
"cfla_files" mapē ir jāiekopē attiecīgie faili, kas norādīti attiecīgajā "config" mapes ini failā.

Projektu iespējams uzstādīt:
1. Kā parasti ielādējot vajadzīgās bibliotēkas (iesakām ar virtuālo vidi).
2. Kā docker konteineri.

### 1. Virtuālā vide
Notestēts ar Python versiju 3.11 un uz augšu
Komandas terminālī 1. izveidos virtuālo vidi, 2. to aktivizēs, ielādēs nepieciešamās bibliotēkas (aizņem kādu laiku):

```
python3 -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  
```

### 2. Docker izstrādes konteineris
Lietotājam jābūt instalētam Docker programmai

#### Lai darbinātu projektu 1. rezi rakstīt terminālī:
```
docker compose up --build
```
#### Pārējās rezies:
```
docker compose up
```
#### Lai apstādinātu koneneri:
```
docker compose down
```

[Jupiter lab saite, kuru var lietot pēc tam]

## Kā izveidot jaunu jautājumu?
[]
## Par citām mapēm un ko tās satur

[answers]
[cfla_files] -
[config]
[dev_config]
[questions]

### scripts mape

#### extractmd.py
Šis fails satur Extractor klasi, kas apstrādā .docx un .pdf formāta dokumentus un pārveido tos markdown formātā, kuru var apstrādāt embedding modelis.

#### finetune_st_embedd.py

#### finetuneembeddings.py

#### gen_precision_report.py

#### gen_results.py
Šis fails ģenerē rezultātu tabulu. Šajā failā tiek apstrādāti visi jautājumi un apakšjautājumi. 
Ja kādam jautājumam norādīts questions.yaml failā ar "check" tad attiecīgais jautājums vai apakšjautājums tiek izlaists. 
Ja uz kādu question0 jautājumu ir atbildēts ar "nē", tad konkrētā jautājumā un visiem apakšjautājumiem ir atbildēts ar "n/a".
Ja uz kādu question0 jautājumu ir atbildēts ar "kontekstā nav informācijas", tad konkrētājā jautājumā un visiem ir atbildēts ar "X".

#### main_report.py

#### my_config_template.py

#### utilities.py
Šajā failā ir dažādas nepieciešamās funkcijas: papildus informācijas iegūšana modelim; jautājumu nodošana modelim un atbildes atgriešana; uzvednes, jautājumu un atbilžu (no answers mapes) iegūšana no konkrētiem failiem, vajadzīgo failu nosaukumu iegūšana no config mapes un to pārveidošana par markdown failiem; saraksts ar jautājumiem, kuri, iespējams, nav atbildāmi.

#### vectorindex.py

[reports]
[supplementary_info]

## License?
Dažādas atsauces, ja tās nepieciešamas?
