![header](doc/header.png)
# Опис
[![PyPI version](https://badge.fury.io/py/uaddress.svg)](https://badge.fury.io/py/uaddress)

Розбирання адреси на типи. Адаптація бібліотеки [usaddress](https://github.com/datamade/usaddress) під українські адреси

> Read this in other language: [English](README.en.md), [Русский](README.md), [Український](README.ua.md)

# Вимоги
* python3
* [parserator](https://github.com/martinjack/parserator)

# Встановлення
```sh
pip3 install uaddress
```
# Встановлення локально
```sh
python3 setup.py install --user
```

# Навчання моделі
```shell
parserator train training/data.xml uaddress
```
### Коли інше розташування моделі
```shell
parserator train training/data.xml uaddress --modelfile anotherpath/uaddr.crfsuite
```

# Тестування моделі
```shell
parserator label training/raw.csv training/data.xml uaddress
```
### Коли інше розташування моделі
```shell
parserator label trainig/raw.csv training/data.xml uaddress --modelfile anotherpath/uaddr.crfsuite
```

# Структура
| Файл                      | Опис                                          |
| :-------------            | :-------------                                |
| training/data.xml         | Набір даних для моделі                        |
| training/raw.csv          | Список адрес для навчання або перевірки       |
| uaddress/uaddr.crfsuite   | NLP модель                                    |

# Приклади
![example1](doc/example1.gif)

## Приклад скрипту
```sh 
python3 example.py
```
![example2](doc/example2.gif)

# Типы
| Назва                     | Опис                                          |
| :-------------            | :-------------                                |
| Country                   | Країна                                        |
| RegionType                | Тип області                                   |
| Region                    | Область                                       |
| CountyType                | Тип району                                    |
| County                    | Район                                         |
| SubLocalityType           | Тип підрайону                                 |
| SubLocality               | Підрайон                                      |
| LocalityType              | Тип населеного пункту                         |
| Locality                  | Населений пункт                               |
| StreetType                | Тип вулиці                                    |
| Street                    | Вулиця                                        |
| HousingType               | Тип корпусу                                   |
| Housing                   | Корпус                                        |
| HostelType                | Тип гуртожитку                                |
| Hostel                    | Гуртожиток                                    |
| HouseNumberType           | Тип номеру будинку                            |
| HouseNumber               | Номер будинку                                 |
| HouseNumberAdditionally   | Додатковий номер будинку                      |
| SectionType               | Тип секції                                    |
| Section                   | Секція                                        |
| ApartmentType             | Тип квартири                                  |
| Apartment                 | Квартира                                      |
| RoomType                  | Тип кімнати                                   |
| Room                      | Кімната                                       |
| Sector                    | Сектор                                        |
| FloorType                 | Тип поверху                                   |
| Floor                     | Поверх                                        |
| PostCode                  | Індекс                                        |
| Manually                  | Набір типів для подальшого розбирання адреси  |
| NotAddress                | Не адреса                                     |
| Comment                   | Коментар                                      |
| AdditionalData            | Додаткові дані                                |