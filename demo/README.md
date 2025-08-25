# Prototips (demo)

Šī mape satur visus datus, kas nepieciešami prototipam. Tā sastāv no divām vidēm izstrādes un produkcijas.
Visām vidēm nepieciešams Docker (https://www.docker.com/), lai tās darbinātu. 
Prototips izmanto daudz skriptus un datus, kas tiek lietoti arī testa vidē, tomēr tie ir modeficēti un nošķirti.
Pieliekot klāt jaunus jautājumus jāatceras tos pielikt arī prototipam, ja ir vēlme tos šeit lietot.

## Kā uzstādīt?
Vispirms ievadīt mainīgos iekš ".env-example" faila un to pārsaukt par ".env".

### 1. Produkcijas vide
Caur komandrinu šajā mapē palaist komandu:
```
./deploy_prod.sh
```
(Papildus var norādit --TAG lai norādītu specifisku versiju)
Šī komanda lejupielādēs Docker attēlus, kas satur mūsu projektu un to iedarbinās. Pēc iedarbināšanas projektu var atrast vientē "**localhost**" - protams, to varētu arī tālāk izmitināt zem kādas citas ip adresses.

### 2. Izstrādes vide
Šo vidi lietot, lai ātrāk testētu un veiktu izstrādi prototipam. Mainot kodu un to saglabājot nav jāpstādina konteineris, tas uzreiz būs pieejams, izņemot ielādētās bibliotēkas.
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

#### Produkcijas vides atjaunošana:
Kad pabeigta izstāde, lietot šo komandu, kas uzbūvēs produkcijas konteineri un to augšupielādēs DockerHub vietnē zem DOCKERHUB_USERNAME lietotāja.
Šo konteineri pēc tam atkal būs iespējams lietot produkcijā.
```
./build_and_push.sh
```
(Papildus var norādit --TAG lai norādītu specifisku versiju)
