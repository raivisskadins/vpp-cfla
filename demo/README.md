# Prototips (demo)

Šī mape satur visus datus, kas nepieciešami prototipam. To iespējams darbināt kā izstrādes vai produkcijas vidi.
Visām vidēm nepieciešams Docker (https://www.docker.com/), lai tās darbinātu. 
Prototips izmanto daudz skriptus un datus, kas tiek lietoti arī testa vidē (galvenā mape), tomēr tie ir modificēti un nošķirti.
Pieliekot klāt jaunus jautājumus jāatceras tos pielikt arī prototipam, ja ir vēlme tos šeit lietot.

## Kā uzstādīt?
Vispirms ievadīt mainīgos iekš .env-example faila un to pārsaukt par .env.

### LLM modelis
Atbilžu ģenerēšanai tiek izmantots Azure OpenAI *gpt-4o* modelis. Lai iegūtu pieeju šim modelim, [portal.azure.com](https://portal.azure.com/) ir jāizveido Azure OpenAI resurss. Pēc tam [Azure OpenAI Studio](https://oai.azure.com/) jāizvēlas *Deployments* un jāizvēlas modelis 'gpt-4o'. Vērtībai *Deployment name* jābūt tādai pašai kā *Model name* - 'gpt-4o'.
 
Skatīt vairāk [šeit](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/overview)
 
.env failā jāieraksta modelim atbilstošās vērtības - AZURE_OPENAI_KEY, AZURE_ENDPOINT un AZURE_OPENAI_VERSION.

### 1. Produkcijas vide
Caur komandrindu šajā mapē palaist komandu:
```
./deploy_prod.sh
```
(Papildus var norādīt --TAG lai norādītu specifisku versiju)
Šī komanda lejupielādēs Docker attēlus, kas satur mūsu projektu un to iedarbinās. Pēc iedarbināšanas projektu var atrast vietnē "**localhost**" - protams, to varētu arī tālāk izmitināt zem kādas citas ip adreses.

### 2. Izstrādes vide
Šo vidi lietot, lai ātrāk testētu un veiktu izstrādi prototipam. Mainot kodu un to saglabājot nav jāapstādina konteineris, tas uzreiz būs pieejams, izņemot ielādētās bibliotēkas.
#### Lai darbinātu projektu 1. reizi rakstīt terminālī:
```
docker compose up --build
```
#### Pārējās reizes:
```
docker compose up
```
#### Lai apstādinātu konteineri:
```
docker compose down
```

#### Produkcijas vides atjaunošana:
Kad pabeigta izstāde, lietot šo komandu, kas uzbūvēs produkcijas konteineri un to augšupielādēs DockerHub vietnē zem DOCKERHUB_USERNAME lietotāja.
Šo konteineri pēc tam atkal būs iespējams lietot produkcijā.
```
./build_and_push.sh
```
(Papildus var norādīt --TAG lai norādītu specifisku versiju)
