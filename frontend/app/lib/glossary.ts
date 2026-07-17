// Slownik pojec: apka TLUMACZY liczby, ktore pokazuje.
//
// Po co w kodzie, a nie z API? Bo to statyczna tresc prezentacyjna, ktora
// zmienia sie razem z UI. Endpoint oznaczalby round-trip, cache, schemat i
// obsluge bledu dla tekstu, ktory i tak jest w buildzie. Jako stala renderuje
// sie w Server Component za darmo.
//
// Kanoniczne definicje ludzkie zyja w CONTEXT.md w korzeniu repo - ten plik
// jest ich wersja dla apki. Zasada: mow, CO liczba znaczy dla decyzji, a nie
// jak sie ja liczy. Kazde haslo ma "policz sam", zeby user mogl sprawdzic
// apke, zamiast jej wierzyc.

export type GlossaryEntry = {
  term: string;
  what: string; // co to jest, po ludzku
  why: string; // czemu Cie to obchodzi
  diy?: string; // jak policzysz sam
};

export const GLOSSARY: Record<string, GlossaryEntry> = {
  zmiennosc: {
    term: "Zmiennosc (roczna)",
    what: "Jak mocno kurs skacze wokol wlasnej sredniej, przeliczone na rok.",
    why: "To miara nerwow, nie kierunku. Wysoka zmiennosc nie znaczy 'spadnie' - znaczy 'bedzie bujac'. Spolka o zmiennosci 50% potrafi zrobic +30% i -30% w tym samym roku.",
    diy: "Odchylenie standardowe dziennych zwrotow × √252 (252 = dni sesyjnych w roku).",
  },
  drawdown: {
    term: "Max drawdown",
    what: "Najgorszy zjazd od szczytu do pozniejszego dolka w badanym okresie.",
    why: "Odpowiada na pytanie, ktorego nie zadaje zaden slupek: 'ile bym stracil, gdybym kupil w najgorszym momencie?'. To liczba, ktora realnie decyduje, czy wytrzymasz i nie sprzedasz w panice.",
    diy: "Dla kazdego dnia: cena / najwyzszy dotychczasowy szczyt − 1. Bierzesz najgorszy wynik.",
  },
  alpha: {
    term: "Alpha (vs rynek)",
    what: "O ile procent pobiles rynek (albo mu przegrales) w tym samym okresie.",
    why: "Sam zwrot +20% nic nie mowi, dopoki nie wiesz, ile dal caly rynek. Jesli rynek dal +25%, Twoje +20% to strata 5 pp - to samo mozna bylo miec taniej i bez wysilku, kupujac indeks.",
    diy: "Twoj zwrot − zwrot benchmarku (tu: SPY) za ten sam okres.",
  },
  beta: {
    term: "Beta",
    what: "Jak mocno spolka rusza sie RAZEM z rynkiem.",
    why: "Beta 1,4 znaczy: gdy rynek spada 10%, ta spolka srednio 14%. Uwaga - to NIE to samo co zmiennosc. Spolka moze bujac 4× mocniej niz rynek i miec bete 1,0, bo buja na WLASNY rachunek (slabo skorelowana z rynkiem).",
    diy: "kowariancja(spolka, rynek) / wariancja(rynku). Rownowaznie: korelacja × (zmiennosc spolki / zmiennosc rynku).",
  },
  pe: {
    term: "P/E (cena / zysk)",
    what: "Ile placisz za kazda zlotowke rocznego zysku spolki.",
    why: "Traktuj to jako RYZYKO WYCENY, nie ocene. P/E 80 znaczy, ze w cenie siedza duze oczekiwania - spolka musi je dowiezc, a jak nie dowiezie, spadek boli podwojnie. Niskie P/E nie znaczy 'okazja': bywa, ze rynek slusznie sie czegos boi.",
    diy: "Cena akcji / zysk na akcje z ostatnich 12 miesiecy. Spolka bez zysku nie ma sensownego P/E.",
  },
  marza: {
    term: "Marza zysku",
    what: "Ile z kazdej zlotowki przychodu zostaje spolce jako zysk.",
    why: "Tu tez patrzymy przez ryzyko: spolka z gruba marza ma bufor na gorsze czasy, a spolka z ujemna marza dokłada do interesu i moze potrzebowac finansowania (emisja akcji = rozwodnienie Twojego udzialu).",
    diy: "Zysk netto / przychody. 0,18 = 18 groszy zysku z kazdej zlotowki sprzedazy.",
  },
  mcap: {
    term: "Kapitalizacja",
    what: "Ile rynek wycenia CALA spolke.",
    why: "Skala mowi o ryzyku wiecej niz branza. Spolka za 500 mln potrafi zrobic ±40% na jednej wiadomosci; gigant za 500 mld rusza sie wolniej, bo trzeba ogromnego kapitalu, zeby nim ruszyc.",
    diy: "Cena akcji × liczba wszystkich akcji.",
  },
  sektor: {
    term: "Sektor i branza",
    what: "Klasyfikacja spolki wg dostawcy danych. Sektor jest szeroki (Energia), branza waska (Uran).",
    why: "Branza jest praktyczniejsza: Cameco ma sektor 'Energia' - jak Orlen - ale branze 'Uran', co mowi duzo wiecej. Uwaga: to klasyfikacja ZRODLA, nie prawda objawiona. Nie kazdy temat jest branza - 'spolki kwantowe' nie istnieja w tej taksonomii.",
  },
  benchmark: {
    term: "Benchmark (SPY)",
    what: "Punkt odniesienia: ETF na indeks S&P 500, czyli 500 najwiekszych spolek USA.",
    why: "To Twoja alternatywa 'nic nie rob': mogles po prostu kupic caly rynek jednym klikiem. Kazdy wybor pojedynczej spolki musi sie z tym mierzyc - inaczej robisz wiecej pracy za mniej pieniedzy.",
  },
};
