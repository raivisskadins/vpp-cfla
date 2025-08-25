# Prototips (demo)

Šī mape satur visus datus, kas nepieciešami prototipam. Tā sastāv no divām vidēm izstrādes un produkcijas.
Visām vidēm nepieciešams Docker (https://www.docker.com/), lai tās darbinātu. 
Prototips izmanto daudz skriptus un datus, kas tiek lietoti arī testa vidē, tomēr tie ir modificēti un nošķirti.
Pieliekot klāt jaunus jautājumus jāatceras tos pielikt arī prototipam, ja ir vēlme tos šeit lietot.

## Kā uzstādīt?
Vispirms ievadīt mainīgos iekš .env-example faila un to pārsaukt par .env.

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
