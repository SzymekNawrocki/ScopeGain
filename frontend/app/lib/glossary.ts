// Glossary: every term the app shows, explained from its origin, with a note on
// whether ScopeGain computes it and free places to check it yourself.
// Rule (ADR-0005): free and good elsewhere -> link; behind a paywall -> built here.
// Keys of criteria match the criterion ids returned by the API.

export type Link = { name: string; url: string; note?: string };

export type GlossaryEntry = {
  term: string;
  group: "Zaufanie" | "Zdrowie" | "Wycena" | "Dywidenda" | "Podatki" | "Dane" | "Poza ScopeGain";
  what: string; // what it is, plainly
  why: string; // where it came from and why it matters for a decision
  computed: "tak" | "nie";
  links?: Link[];
};

const SEC_SEARCH: Link = {
  name: "SEC EDGAR",
  url: "https://www.sec.gov/edgar/search/",
  note: "oryginalne raporty 10-K, za darmo",
};
const STOCKANALYSIS: Link = {
  name: "stockanalysis.com",
  url: "https://stockanalysis.com/",
  note: "5 lat sprawozdań i 10 lat dywidend za darmo",
};
const BIZNESRADAR_RATING: Link = {
  name: "Biznesradar — rating GPW",
  url: "https://www.biznesradar.pl/spolki-rating/akcje_gpw",
  note: "Piotroski F-Score i Altman EM-Score dla spółek z GPW",
};

export const GLOSSARY: Record<string, GlossaryEntry> = {
  beneish: {
    term: "Beneish M-Score",
    group: "Zaufanie",
    what: "Jedna liczba z ośmiu wskaźników, która mówi, czy wyniki spółki wyglądają na podrasowane.",
    why: "Messod Beneish w 1999 r. przebadał spółki złapane przez SEC na manipulacji i sprawdził, czym ich liczby różniły się od uczciwych: należności rosły szybciej niż sprzedaż, zysk nie szedł w parze z gotówką, marże się kurczyły. Wynik powyżej −1,78 znaczy: liczby przypominają manipulatorów. ScopeGain wtedy wyklucza spółkę, bo żadna inna liczba nie ma sensu, jeśli nie można ufać raportowi.",
    computed: "tak",
    links: [SEC_SEARCH],
  },
  piotroski: {
    term: "Piotroski F-Score",
    group: "Zaufanie",
    what: "Dziewięć pytań tak/nie o rentowność, zadłużenie i efektywność. Wynik 0–9.",
    why: "Joseph Piotroski w 2000 r. szukał sposobu, by wśród tanich spółek odsiać te tanie słusznie (bo słabe) od tych tanich niesłusznie. Zamiast prognoz zadał proste pytania: czy spółka zarabia, czy zysk jest w gotówce, czy dług spada, czy nie dodrukowuje akcji. Spółki z 8–9 punktami biły rynek, te z 0–1 wypadały najgorzej. Liczy się z trzech ostatnich lat sprawozdań.",
    computed: "tak",
    links: [BIZNESRADAR_RATING],
  },
  altman: {
    term: "Altman Z-Score",
    group: "Zaufanie",
    what: "Ryzyko bankructwa w horyzoncie około 2 lat, w jednej liczbie ze strefami: bezpieczna, szara, zagrożenia.",
    why: "Edward Altman w 1968 r. porównał 33 spółki, które zbankrutowały, z 33 podobnymi, które przetrwały, i znalazł pięć wskaźników, które je rozdzielały: kapitał obrotowy, zyski zatrzymane, zysk operacyjny, wycena wobec długów i sprzedaż wobec majątku. Wersja Z dotyczy producentów, wersja Z'' (1995) pozostałych spółek. Nie dotyczy banków.",
    computed: "tak",
    links: [BIZNESRADAR_RATING],
  },
  dilution: {
    term: "Rozwadnianie akcji",
    group: "Zaufanie",
    what: "O ile procent rocznie rośnie liczba akcji spółki.",
    why: "Gdy spółka dodrukowuje akcje (emisje, opcje dla zarządu), ten sam zysk dzieli się na więcej kawałków, a Twój kawałek się kurczy. Pontiff i Woodgate (2008) pokazali, że spółki emitujące akcje potem wypadają gorzej. Skup akcji działa odwrotnie.",
    computed: "tak",
  },
  net_debt_ebitda: {
    term: "Dług netto / EBITDA",
    group: "Zdrowie",
    what: "Ile lat zysku operacyjnego (przed amortyzacją) potrzeba, by spłacić dług pomniejszony o gotówkę.",
    why: "To język agencji ratingowych. S&P uznaje poniżej 3 za zadłużenie umiarkowane, powyżej 4 za agresywne. Przy wysokim długu wystarczy jeden słaby rok, by spółka musiała ciąć dywidendę albo emitować akcje.",
    computed: "tak",
    links: [STOCKANALYSIS],
  },
  interest_coverage: {
    term: "Pokrycie odsetek",
    group: "Zdrowie",
    what: "Ile razy zysk operacyjny (EBIT) mieści w sobie roczne odsetki od długu.",
    why: "Aswath Damodaran z NYU przypisał przedziałom tego wskaźnika oceny ratingowe. Około 2,5 i więcej to poziom spółek z oceną inwestycyjną (BBB i wyżej), poniżej 1,5 to obligacje śmieciowe.",
    computed: "tak",
    links: [
      {
        name: "Damodaran — tabela ratingów",
        url: "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html",
      },
    ],
  },
  current_ratio: {
    term: "Płynność bieżąca",
    group: "Zdrowie",
    what: "Aktywa bieżące (gotówka, należności, zapasy) podzielone przez zobowiązania do spłaty w ciągu roku.",
    why: "Benjamin Graham, nauczyciel Warrena Buffetta, wymagał od spółek dla ostrożnego inwestora co najmniej 2: majątek krótkoterminowy dwa razy większy niż krótkoterminowe długi. Poniżej 1 spółka może mieć kłopot z zapłaceniem rachunków.",
    computed: "tak",
  },
  op_margin_pct: {
    term: "Marża operacyjna na tle branży",
    group: "Zdrowie",
    what: "Jaki procent sprzedaży zostaje po kosztach działalności, porównany ze spółkami z tym samym kodem branży (SIC).",
    why: "Sama marża 10% nic nie mówi: w handlu to świetnie, w oprogramowaniu słabo. Percentyl pokazuje, czy spółka jest lepsza od konkurencji, bez niczyjej opinii o tym, jaka marża jest „dobra”.",
    computed: "tak",
  },
  roa_pct: {
    term: "ROA na tle branży",
    group: "Zdrowie",
    what: "Zysk netto podzielony przez cały majątek spółki, porównany z branżą.",
    why: "Mówi, jak dobrze zarząd zamienia majątek w zysk. Percentyl na tle branży usuwa różnice między sektorami, które z natury potrzebują dużo albo mało majątku.",
    computed: "tak",
  },
  graham_multiplier: {
    term: "Mnożnik Grahama (C/Z × C/WK)",
    group: "Wycena",
    what: "Cena do zysku pomnożona przez cenę do wartości księgowej. Graham uznawał za rozsądne co najwyżej 22,5.",
    why: "W „Inteligentnym inwestorze” Graham chciał płacić nie więcej niż 15 razy zysk i 1,5 raza majątek księgowy, ale dopuszczał wymianę: wyższe C/Z przy niskim C/WK i odwrotnie. Stąd 15 × 1,5 = 22,5. Spółki technologiczne prawie zawsze ten test oblewają: to fakt o ich wycenie, nie błąd.",
    computed: "tak",
    links: [STOCKANALYSIS],
  },
  pe_vs_history: {
    term: "C/Z na tle własnej historii",
    group: "Wycena",
    what: "Dzisiejsza cena do zysku porównana z tym, ile rynek płacił za zysk tej samej spółki w poprzednich latach.",
    why: "Każda spółka ma swój „normalny” poziom wyceny. Porównanie z własną historią odpowiada na pytanie: kupuję teraz taniej czy drożej niż zwykle? ScopeGain koryguje dawny zysk na akcję o splity, żeby porównywać jabłka z jabłkami.",
    computed: "tak",
    links: [STOCKANALYSIS],
  },
  payout_fcf: {
    term: "Dywidenda / wolne przepływy (FCF)",
    group: "Dywidenda",
    what: "Jaką część wolnej gotówki (przepływy operacyjne minus inwestycje) spółka wypłaca jako dywidendę.",
    why: "Zysk księgowy można upiększyć, gotówki nie. Jeśli dywidenda przekracza wolną gotówkę, spółka płaci z długu albo z rezerw, a tak nie da się w nieskończoność. To częsty sygnał przed cięciem dywidendy.",
    computed: "tak",
    links: [STOCKANALYSIS],
  },
  dividend_streak: {
    term: "Lata bez cięcia dywidendy",
    group: "Dywidenda",
    what: "Ile kolejnych pełnych lat regularna dywidenda na akcję nie spadła.",
    why: "Indeksy „Dividend Achievers” (10+ lat podwyżek) i „Dividend Aristocrats” (25+ lat) zbierają spółki, które utrzymały dywidendę przez recesje. Długa seria to dowód, że zarząd traktuje dywidendę jak zobowiązanie.",
    computed: "tak",
    links: [STOCKANALYSIS],
  },
  w8ben: {
    term: "W-8BEN",
    group: "Podatki",
    what: "Amerykański formularz, którym potwierdzasz, że jesteś rezydentem podatkowym Polski.",
    why: "Bez niego USA pobiera 30% od dywidendy. Z nim, dzięki umowie PL-USA, pobiera 15%. Broker przyjmuje go zwykle elektronicznie; ważny jest około 3 lat.",
    computed: "nie",
    links: [{ name: "IRS — Form W-8BEN", url: "https://www.irs.gov/forms-pubs/about-form-w-8-ben" }],
  },
  wht: {
    term: "Podatek u źródła i dopłata w PIT-38",
    group: "Podatki",
    what: "Podatek pobrany w kraju spółki przy wypłacie dywidendy oraz polska dopłata do 19%.",
    why: "Polska bierze 19% od dywidendy, ale pozwala odliczyć podatek zapłacony za granicą tylko do stawki z umowy (dla USA 15%). Zostaje dopłata 4% w PIT-38, sekcja G. Netto: 81% z W-8BEN, 66% bez.",
    computed: "tak",
    links: [{ name: "podatki.gov.pl", url: "https://www.podatki.gov.pl/pit/" }],
  },
  nbp_rate: {
    term: "Kurs NBP z dnia przed wypłatą",
    group: "Podatki",
    what: "Kurs średni NBP z ostatniego dnia roboczego przed wypłatą dywidendy, po którym przeliczasz ją na złote do PIT.",
    why: "Tak każe ustawa o PIT. ScopeGain do prognozy używa bieżącego kursu, bo przyszłego nikt nie zna.",
    computed: "tak",
    links: [{ name: "NBP — kursy walut", url: "https://nbp.pl/" }],
  },
  percentile: {
    term: "Percentyl",
    group: "Dane",
    what: "Jaki odsetek porównywanych spółek ma gorszy wynik. 80. percentyl = lepiej niż 80% branży.",
    why: "To statystyka bez opinii: nikt nie musi ustalać, jaka marża jest „dobra”, bo porównujemy z faktycznym rozkładem w branży.",
    computed: "tak",
  },
  sic: {
    term: "Kod SIC",
    group: "Dane",
    what: "Czterocyfrowy kod branży, który SEC nadaje każdej spółce (np. 3571 = komputery).",
    why: "ScopeGain wyznacza nim konkurencję do percentyli. Kod bywa szeroki albo przestarzały, więc porównanie z branżą to przybliżenie.",
    computed: "tak",
    links: [SEC_SEARCH],
  },
  gpw: {
    term: "Spółki z GPW",
    group: "Poza ScopeGain",
    what: "ScopeGain analizuje tylko spółki raportujące do SEC (USA).",
    why: "Dla GPW nie ma darmowego API ze sprawozdaniami. Biznesradar za darmo liczy F-Score i Altmana dla polskich spółek, więc tam odsyłamy, zamiast budować to od nowa.",
    computed: "nie",
    links: [BIZNESRADAR_RATING, { name: "Biznesradar", url: "https://www.biznesradar.pl/" }],
  },
  etf: {
    term: "ETF-y: domicyl, TER, akumulacja",
    group: "Poza ScopeGain",
    what: "Fundusz ETF ocenia się innymi miarami niż spółkę: kosztem rocznym (TER), krajem rejestracji i tym, czy reinwestuje dywidendy.",
    why: "Dla Polaka kluczowy jest domicyl: ETF z Irlandii płaci 15% podatku od dywidend z USA, a z Luksemburga 30%. Fundusz akumulujący nie wypłaca dywidend, więc nie płacisz od nich podatku co roku. justETF pokazuje to wszystko za darmo.",
    computed: "nie",
    links: [{ name: "justETF", url: "https://www.justetf.com/" }],
  },
  ike_ikze: {
    term: "IKE i IKZE",
    group: "Poza ScopeGain",
    what: "Opakowania na rachunek maklerski z ulgą podatkową na emeryturę.",
    why: "IKE: brak Belki przy wypłacie po 60. roku życia, wcześniej jak zwykły rachunek. IKZE: odliczenie wpłat od PIT teraz, 10% przy wypłacie po 65. Ani IKE, ani IKZE nie zwalniają z amerykańskiego podatku u źródła.",
    computed: "nie",
    links: [{ name: "podatki.gov.pl", url: "https://www.podatki.gov.pl/pit/" }],
  },
  screener: {
    term: "Screener i wykresy",
    group: "Poza ScopeGain",
    what: "Filtrowanie wielu spółek naraz po wskaźnikach i wykresy kursów.",
    why: "Robią to dobrze i za darmo inni, więc ScopeGain tego nie powtarza. Sens ScopeGain to głęboki werdykt dla jednej spółki.",
    computed: "nie",
    links: [
      { name: "Finviz — screener", url: "https://finviz.com/screener.ashx" },
      { name: "TradingView — wykresy", url: "https://www.tradingview.com/" },
    ],
  },
};
