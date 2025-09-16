# Mākslīgā intelekta metožu piemērotības analīze Eiropas Savienības fondu projektu jomā (VPP-CFLA)
Valsts pētījumu programmas ietvaros tiek īstenots projekts "[Mākslīgā intelekta metožu piemērotības analīze Eiropas Savienības fondu projektu jomā](https://www.cfla.gov.lv/lv/projekts/maksliga-intelekta-metozu-piemerotibas-analize-eiropas-savienibas-fondu-projektu-joma)". Tā īstenošanu koordinē Latvijas Zinātnes padome, par projekta īstenošanu atbildīgā institūcija - Centrālā finanšu līgumu aģentūra.
Projekta galvenais mērķis ir novērtēt ģeneratīvā mākslīgā intelekta (ĢMI) piemērotību un efektivitāti Eiropas Savienības (ES) fondu projektu iepirkumu dokumentācijas analīzē. Projekta ietvaros tiks pētīti dažādi ĢMI risinājumi, analizējot to spēju apstrādāt iepirkumu dokumentāciju tekstus. Projekta rezultātā tiks izstrādāts prototips, kas demonstrēs ĢMI pielietošanas iespējas iepirkumu analīzes procesu automatizācijā un sagatavoti rīcībpolitikas ieteikumi ĢMI risinājumu izmantojumam ES fondu projektu uzraudzības procesos.

Šajā repozitorijā ir: 1) pētniecības programmatūra, kas izmantota projekta eksperimentiem, un 2) praktisks [prototips](demo), ko var izmantot rezultātu izvērtēšanai.
Papildus programmatūrai šajā repozitorijā ir pieejamas arī datu kopas, kas izmantotas eksperimentos. Datu kopas sastāv no 30 iepirkumu dokumentiem, kurus novērtējuši CFLA eksperti. Ekspertu sagatavotās iepirkumu pārbaudes lapas ir pārveidotas mašīnlasāmā formātā. Par katru iepirkumu tiek uzdoti 168 jautājumi par tā atbilstību likumdošanai, un pie katra jautājuma ir norādīta atbilde. Datu kopa ir sadalīta divās apakškopās: izstrādes datu kopa (10 iepirkumi) un novērtēšanas datu kopa (20 iepirkumi). Datu kopas veido: 1) jautājumi [questions](questions) mapē, kas veidoti uz pārbaudes lapas S.7.1.-PL-21 (09.12.2019. redakcija) pamata; 2) marķēta datu kopa [answers](answers) mapē, kas atbilst 30 CFLA izvērtētiem iepirkumiem.

## Eksperimentu programmatūra

Galvenais eksperimentos izmantotais skripts ir izveidots kā Python Notebook — [ProjectProcurementReview.ipynb](ProjectProcurementReview.ipynb).  
Papildu skripti, kas nepieciešami tā darbināšanai, atrodas mapē [scripts](scripts) kā atsevišķi Python faili.
Faktiski eksperimentu programmatūru veido viss kods, izņemot *demo* mapi. 
Sistēma ir izstrādāta, izmantojot izguves papildinātas ģenerēšanas (RAG) algoritmu dokumentācijas pārbaudei ar lielo valodas modeli (LLM).


Palaižot skriptu, 
- tas iziet cauri visiem iepirkumu failiem, kas ietilpst izvēlētajā eksperienta konfigurācijā (novērtēšanas datu kopas konfigurācija atrodas [config](config) mapē, izstrādes datu kopas konfigurācija - [dev_config](dev_config)), veicot sekojošas darbības:
	- no iepirkuma un līguma projekta faila tiek izgūts teksts markdown formātā;
	- teksts tiek sadalīts fragmentos un fragmentiem atbilstošie vektori tiek pievienoti vektoru bāzei;
	- katram jautājumam no saraksta
	  - no vektoru bāzes tiek izgūti semantiski līdzīgākie fragmenti;
	  - tiek veidota uzvedne ar jautājumam līdzīgākajiem fragmentiem, jautājumu un papildu informāciju no likumiem;
	  - uzvedne tiek nosūtīta uz LLM modeli, kas ģenerē atbildi;
	  - atbilde tiek salīdzināta ar sagaidāmo atbildi no marķētā atbilžu faila;
	- atbildes tiek saglabātas .csv un .html formātu atskaišu failos, kuros ir apskatāma sīka informācija par katru jautājumu;
- tiek izveidota visiem pārbaudītajiem iepirkumiem kopēja atskaite *main_report.html*, kurā var aplūkot pārskatāmāku sarakstu ar iepirkumiem, saraksta rindiņas iespējams izvērst un apskatīt visus jautājumus detalizēti; 
- tiek izveidota atskaite *precision_report.html* , kurā var apskatīt katra apstrādātā jautājuma precizitāti un papildu novērtēšanas datus par apstrādes sniegumu;
- tiek izveidots arī *report.htm* fails, kas ir iepriekš lietotā *report.csv* HTML versija.

Ar *PromptTest.ipynb* skriptu iespējams notestēt individuālas uzvednes.

_Ir izstrādāti skripti ar kuriem iespējams iegūt pielāgotu embedding modeli šāda veida sistēmai (uzlabojot tā rezultātu), un projekta ietvarā ir pielāgots šāds modelis, kas ir pieejams prototipā._

## Prototips
Atrodas mapē [demo](demo). Informāciju par tā uzstādīšanu un lietošanu meklēt *demo* mapes [README.md](demo\README.md).

## Uzstādīšana
Sistēmas darbināšanai nepieciešama pietiekami stipra darba stacija - vismaz 16GB RAM un vēlams arī laba video karte.
Pirms darba uzsākšanas nepieciešams aizpildīt .env-example failu ar pareizajām vertībām un pārsaukt to uz -> .env

*cfla_files* mapē ir jāiekopē faili, kas norādīti attiecīgajā *config* mapes .ini failā.

### LLM modelis
Atbilžu ģenerēšanai tiek izmantots Azure OpenAI *gpt-4o* modelis. Lai iegūtu pieeju šim modelim, [portal.azure.com](https://portal.azure.com/) ir jāizveido Azure OpenAI resurss. Pēc tam [Azure OpenAI Studio](https://oai.azure.com/) jāizvēlas *Deployments* un jāizvēlas modelis 'gpt-4o'. Vērtībai *Deployment name* jābūt tādai pašai kā *Model name* - 'gpt-4o'.
 
Skatīt vairāk [šeit](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/overview)
 
.env failā jāieraksta modelim atbilstošās vērtības - AZURE_OPENAI_KEY, AZURE_ENDPOINT un AZURE_OPENAI_VERSION.

### Projekta darbināšana
Projektu iespējams darbināt:
1. Ielādējot vajadzīgās bibliotēkas (iesakām ar virtuālo vidi) un startējot *jupyter lab* vidi.

2. Kā docker konteineri.

### 1. Virtuālā vide
Notestēts ar Python versiju 3.11 un uz augšu.
Komandas terminālī 1) izveidos virtuālo vidi; 2) to aktivizēs, ielādēs nepieciešamās bibliotēkas (aizņem kādu laiku); 3) startēs *jupyter lab*:

```
python3 -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  
jupyter lab
```

### 2. Docker izstrādes konteineris
Lietotājam jābūt instalētam Docker programmai.

- Lai darbinātu projektu pirmo reizi, vispirms ir jāsabūvē docker konteineris. Ierakstot terminālī šādu komandu, konteineris tiek sabūvēts un startēts:
```
docker compose up --build
```
- Pārējās reizies atkārtoti pārbūvēt projektu nav nepieciešams, to var startēt ar šādu komandu:
```
docker compose up
```
- Konteineri var apstādināt ar šādu komandu:
```
docker compose down
```

## Kā izveidot jaunu jautājumu?

(Gadījumā, ja ir nepieciešams veikt pārbaudi, papildinot vai mainot jautājumu kopu.)

**Failā *questions/questions.yaml* var ierakstīt jaunu jautājumu ar tādu pašu struktūru kā eksistējošiem jautājumiem (ievērojot atstarpes):**
```
- nr: [jautājuma numurs]
  prompt-id: [uzvednes id numurs (No questions/prompts.yaml faila. Šī rinda nav obligāta - ja to atstāj tukšu tiks lietos prompt-id 0.)]
  question: "[jauna jautājuma teksts (pēdiņās)]"
```
Ja jautājuma atbildei nepieciešami izvilkumi no likumiem (PIL vai MK107), tos var norādīt šādā veidā:
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

**Ir jāieraksta arī atbildes jaunam jautājumam atbilžu failos. Tām jābūt ar tādu pašu struktūru kā citām atbildēm (ievērojot atstarpes).**
- Demo vidē - failā *backend/template.yaml* jāieraksta tukša atbilde ar jaunā jautājuma numuru:
```
- nr: [jautājuma numurs]
  answer: ""
```
- Testa vidē - visos failos answers mapē, kurus plānots izmantot, jāieraksta jaunā jautājuma numurs un atbilde ("jā" vai "nē" vai "n/a"):
```
- nr: [jautājuma numurs]
  answer: "[atbilde (pēdiņās)]"
```

**Ja jautājums ir jautājumu grupas apakšpunkts, tas jāievieto failā pie attiecīgas grupas. Atstarpju skaitam YAML failos jābūt tādam pašam kā citiem jautājumiem grupā. Tas ir attiecināms arī uz atbildēm, ko ieraksta atbilžu failos.**

**Ja jautājums sastāv no divām daļām, kur pirmai daļai jāizpildās, lai jautājums būtu attiecināms, to var ierakstīt kā divus jautājumus, piemēram:**
- Jautājumu failā (questions.yaml), pie question:
```
  question0: "[nosacījuma jautājuma teksts, kuram jāizpildās, lai viss jautājums būtu attiecināms (pēdiņās)]"
  prompt0-id: [uzvednes id numurs apakšjautājumam, nav obligāts]
```
- Atbilžu failā, pie answer:
```
  answer0: "[atbilde apakšjautājumam]"
```

## Par citu mapju saturu

### *answers* mape

Satur sagaidāmo atbilžu failus. Tie tiek izmantoti, lai vērtētu sistēmas precizitāti.

### *cfla_files* mape

Satur nolikumu un līguma projektu oriģinālos dokumentus un novērtējuma lapas. No tiem tiek izgūts konteksts modelim.

### *config* mape

Satur konfigurācijas failus, kas norāda uz nolikumu un līguma projektu dokumentiem un tiem atbilstošiem atbilžu failiem. Šajā mapē ir konfigurācijas faili projektiem, kas tika izmantoti testēšanai (testa datu kopa).

### *dev_config* mape

Satur konfigurācijas failus, kas norāda uz nolikumu un līguma projektu dokumentiem un tiem atbilstošiem atbilžu failiem. Šajā mapē ir konfigurācijas faili projektiem, kas tika izmantoti izstrādei (validācijas datu kopa).

### *questions* mape

Satur jautājumu failu *questions.yaml*, oriģinālo jautājumu failu *original.yaml* un uzvedņu failu *prompts.yaml*. Jautājumu fails satur jautājumus, kuri ir adaptēti no CFLA pārbaudes lapām, un norādes uz apstrādei nepieciešamajiem datiem. Jautājumi un uzvednes tiek izmantoti, sūtot pieprasījumus uz LLM.

### *scripts* mape

 - *extractmd.py*
 
Šis fails satur Extractor klasi, kas apstrādā .docx un .pdf formāta dokumentus un pārveido tos markdown formātā, kuru var apstrādāt embedding modelis.

 - *gen_precision_report.py*
 
Šis skripts izveido *precision_report.html* faila saturu, kur funkcijas atgriež html kodu, katra apstrādātā jautājuma precizitātes un papildu novērtēšanas datus.

 - *gen_results.py*
 
Šis fails ģenerē rezultātu tabulu. Šajā failā tiek apstrādāti visi jautājumi un apakšjautājumi. 
Ja kādam jautājumam norādīts *questions.yaml* failā ar "check" tad attiecīgais jautājums vai apakšjautājums tiek izlaists. 
Ja uz kādu *question0* jautājumu ir atbildēts ar "nē", tad konkrētā jautājumā un visiem apakšjautājumiem tiek atbildēts ar "n/a".
Ja uz kādu *question0* jautājumu ir atbildēts ar "kontekstā nav informācijas", tad konkrētajā jautājumā un visiem tiek atbildēts ar "X".

 - *main_report.py*
 
Šis skripts ģenerē *main_report.html* failu ar html kodu, rezultātu tabulu un skriptu tabulas funkcionalitātei. 

 - *my_config_template.py*
 
Šis fails ir paraugs *my_config.py* faila izveidei. Tas ir nepieciešams, lai, mainot parametrus *ProjectProcurementReview.ipynb* failā un daloties ar izmaiņām, citiem izstrādātājiem nebūtu "merge conflict" šo parametru dēļ. Lai izmantotu failu, tas ir jāpārsauc par *my_config.py*.

 - *utilities.py* 
 
Šajā failā ir dažādas nepieciešamās funkcijas: papildu informācijas iegūšana modelim; jautājumu nodošana modelim un atbildes atgriešana; uzvednes, jautājumu un atbilžu (no answers mapes) iegūšana no konkrētiem failiem, vajadzīgo failu nosaukumu iegūšana no config mapes un to pārveidošana par markdown failiem; saraksts ar jautājumiem, kuri, iespējams, nav atbildami.

 - *vectorindex.py* 
 
Šajā failā ir QnAEngine klase, kas sadala dokumentus mazākos fragmentos (chunks), ģenerē un saglabā to vektorus, lai paātrinātu atkārtotu izmantošanu; izveido vektoru indeksu; veic jautājumu apstrādi un atbilžu atgriešanu.

 - *gen_finetuning_data.py* 
 
Skripts ģenerē pielāgošanas datus vektorizēšanas modelim, izmantojot *gpt-4o* modeli. No [Iepirkumu sistēmas vietnes](https://www.eis.gov.lv/EKEIS/Supplier) izgūtie dokumenti tiek fragmentēti, izmantojot funkcijas no skriptiem *extractmd.py* un *vectorindex.py*, un katram fragmentam tiek ģenerēti jautājumi.

 - *finetune_st_embedd.py* 
 
Skripts veic vektorizēšanas modeļa *bge-m3* pielāgošanu, izmantojot sintētiskus datus.

### *reports* mape 

Šajā mapē atrodas projektā veikto eksperimentu rezultāti. Atskaites ir nosauktas pēc identifkatora un datuma, kad veikts tests. Atskaites sastāv no galvenajiem rezultātu datiem failā *report.csv* un testa parametriem failā *config.json*. Vizualizēti rezultāti par katru apstrādāto iepirkumu ar sagaidāmajiem un iegūtajiem rezultātiem, paskaidrojuma un pilnajām uzvednēm atrodami failā *main_report.html*. Precizitātes rādītāji katram jautājumam ir failā *precision_report.html*. 

Tiek izmantotas trīs precizitātes metrikas: 
1. **precision** - galvenā precizitāte, kas tiek mērīta, salīdzinot, vai sagaidāmā atbilde sakrīt ar iegūto. *Total_asked / n_correct*. *Total_asked* - jautājumu skaits, kas tika apstrādāti. To var būt mazāk par jautājumu skaitu, jo dažiem iepirkumiem kāds jautājums var būt izlaists - tad sagaidāmā atbilde ir "?". 
2. **precision_answered** - šīs precizitātes mērķis ir parādīt, cik sistēma labi darbotos, ja ņemtu vērā tikai tās atbildes, kur LLM modelis ir pārliecināts par savu atbildi, atbildot ar "jā" vai "nē". Precizitāte tiek mērīta, atņemot tos jautājumus, kuros atbilde ir "kontekstā nav informācija". *total_answered / n_correct*.
3. **precision_answered_wo_na** - precizitātes mērķis ir parādīt, kāda ir maksimālā iespējamā precizitāte, kādu iespējams iegūt ar šo sistēmu, pieņemot, ka datos nav jautājumu, kuri nav atbildami. Šobrīd ir tādi jautājumi, kuriem sagaidāmā atbilde ir "n/a", bet LLM nav dota iespēja atbildēt šādi. Precizitāte tiek rēķināta šādi - *total_answered_wo_na / n_correct*. *total_answered_wo_na* - iegūta saskaitot tos jautājumus, kuriem atbildē nebija "kontekstā nav informācija" un kuri bija atbildami.

### *supplementary_info* mape

Satur dokumentus ar dažādu likumu tekstu, kas tiek iekļauts LLM uzvednē.

## Third-Party Software

This project relies on third-party software components.  
A complete list of dependencies, including versions, licenses, and sources, is provided in [SRF-VPP-CFLA.md](SRF-VPP-CFLA.md).

## License

This project is licensed under the [Apache License 2.0](LICENSE). [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

### Copyright

© 2025 State Research Programme project *"Analysis of the Applicability of Artificial Intelligence Methods in the Field of European Union Fund Projects"*  
(Project number: **VPP-CFLA-Mākslīgais intelekts-2024/1-0003**).  
The project is implemented by the University of Latvia.
