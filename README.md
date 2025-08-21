# VPP CFLA

[Kāds ir projekta mērķis, kas tajā ir izdarīts - marķēti dati, LLM + RAG sistēma, embedding modeļu fine-tuning]

## Projekta sastāvdaļas
[Galvenā informācija]
Projekts sastāv no 2 vidēm testa un demo.
Testa vidē ietilpst viss, izņemot demo mape, kas ir demo videi.
Informāciju par demo vides uzstādīšanu un lietošanu meklēt demo mapes README.MD

Testa vides galvenais darbināmais skripts ir "ProjectProcurementReview.ipynb"
[Ko tas dara?]
[Par my_config_template.py]

"PromptTest.ipynb" iespējams notestēt individuālas uzvednes

## Kā uzstādīt?
Sistēmas darbināšanai nepieciešama pietiekami stipra darba stacija. Iesakāms, ka lietotājam ir vismaz 16GB RAM un vēlams arī laba video karte.
Vispirms nepieciešams aizpildīt .env-example failu ar pareizajām vertībām un pārsaukt uz -> .env
"cfla_files" mapē ir jāiekopē attiecīgie faili, kas norādīti attiecgīgajā "config" mapes ini failā.

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

## Par citām mapēm un ko tās satur

[answers]
[cfla_files] - 

## License?
Dažādas atsauces, ja tās nepieciešamas?
