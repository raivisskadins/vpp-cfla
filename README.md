# VPP CFLA
Šis projekts satur prototipa (demo) risinājumu un dažādus eksperimentus, kas saistīti ar CFLA iepirkuma dokumentācijas pārbaudes sistēmas darbināšanu lietojot LLM ar RAG.
Projekts satur autoru marķētu datukopu "answers" mapē, kas atbilst 30 CFLA iepirkumiem, kuri ir izvērtēti. Ir izstrādāti skripti ar kuriem iespējams iegūt pielāgotu embedding modeli šada veida sistēmai (uzlabojot tā rezultātu), un projekta ietvarā ir pielāgots šāds modelis, kas ir pieejams prototipā.

## Projekta sastāvdaļas
Projekts sastāv no 2 vidēm testa un prototipa (demo).
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

#### Lai darbinātu projektu 1. reizi rakstīt terminālī:
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

## Kā izveidot jaunu jautājumu?

**Failā questions/questions.yaml var ierakstīt jaunu jautājumu ar tādu pašu struktūru kā eksistējošiem jautājumiem (ievērojot atstarpes):**
```
- nr: [jautājuma numurs]
  prompt-id: [uzvednes id numurs (No questions/prompts.yaml faila. Šī rinda nav obligāta - ja to atstāj tukšu tiks lietos prompt-id 0.)]
  question: "[jauna jautājuma teksts (pēdiņās)]"
```
Ja jautājuma atbildei nepieciešami likumi kā PIL vai MK107, tos var norādīt šādā veidā:
```
  PIL:
   - chapter: [panta numurs]
     pt:
      - [nodaļas numurs]
```
```
  MK107:
   - chapter: [panta numurs]
```

**Arī jāieraksta atbildes jaunam jautājumam atbilžu failos, ar tādu pašu struktūru kā citām atbildēm (ievērojot atstarpes).**
- Demo vidē - failā backend/template.yaml jāieraksta tukša atbilde ar jaunā jautājuma numuru:
```
- nr: [jautājuma numurs]
  answer: ""
```
- Testa vidē - visos failos answers mapē, kurus plānots izmantot, jāieraksta jaunā jautājuma numurs un atbilde ("jā" vai "nē" vai "n/a"):
```
- nr: [jautājuma numurs]
  answer: "[atbilde (pēdiņās)]"
```

**Ja jautājums ir jautājumu grupas apakšpunkts, tas jāievieto failā pie attiecīgas grupas. Atstarpju skaits YAML failiem jābūt tāds pats ka citiem jautājumiem grupā. Tas ir attiecināms arī uz atbildēm, ko ieraksta atbilžu failos.**

**Ja jautājums sastāv no divām daļām, kur pirmai daļai jābūt izpildītai, lai jautājums būtu attiecināms, to var ierakstīt kā divus jautājumus, kā piemēram:**
- Jautajumu failā (questions.yaml), pie question:
```
  question0: "[nosacījuma jautājuma teksts, kuram jābūt izpildītam, lai viss jautājums būtu attiecināms (pēdiņās)]"
  prompt0-id: [uzvednes id numurs apakšjautājumam, nav obligāts]
```
- Atbilžu failā, pie answer:
```
  answer0: "[atbilde apakšjautājumam]"
```

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
Šis skripts izveido precision_report.html faila saturu, kur funkcijas atgriež html kodu, katra apstrādātā jautājuma precizitātes un papildus novērtēšanas datus.

#### gen_results.py
Šis fails ģenerē rezultātu tabulu. Šajā failā tiek apstrādāti visi jautājumi un apakšjautājumi. 
Ja kādam jautājumam norādīts questions.yaml failā ar "check" tad attiecīgais jautājums vai apakšjautājums tiek izlaists. 
Ja uz kādu question0 jautājumu ir atbildēts ar "nē", tad konkrētā jautājumā un visiem apakšjautājumiem ir atbildēts ar "n/a".
Ja uz kādu question0 jautājumu ir atbildēts ar "kontekstā nav informācijas", tad konkrētājā jautājumā un visiem ir atbildēts ar "X".

#### main_report.py
Šis skripts izveido main_report.html faila saturu, kurā tiek izveidots html kods, rezultātu tabula un skripts tabulas funkcionalitātei. 

#### my_config_template.py
Šis fails ir paraugs my_config.py faila izveidei. Šāds fails ir nepieciešams, lai, mainot parametrus ProjectProcurementReview.ipynb failā un daloties ar izmaiņām, citiem izstrādātājiem nebūtu "merge conflict" šo parametru dēļ.

#### utilities.py
Šajā failā ir dažādas nepieciešamās funkcijas: papildus informācijas iegūšana modelim; jautājumu nodošana modelim un atbildes atgriešana; uzvednes, jautājumu un atbilžu (no answers mapes) iegūšana no konkrētiem failiem, vajadzīgo failu nosaukumu iegūšana no config mapes un to pārveidošana par markdown failiem; saraksts ar jautājumiem, kuri, iespējams, nav atbildāmi.

#### vectorindex.py
Šajā failā ir QnAEngine klase, kas akcentē markdown failā virsrakstus; sadala dokumentus mazākos fragmentos (chunks), ģenerē to embeddings un saglabā cache, lai paātrinātu atkārtotu izmantošanu; izveido vektoru indeksu; veic jautājumu apstrādi un atbilžu atgriešanu.

### reports mape

### supplementary_info mape

## License?
Dažādas atsauces, ja tās nepieciešamas?
