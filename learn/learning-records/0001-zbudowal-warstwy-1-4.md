# Zbudował i zweryfikował warstwy 1–4 (API → baza → front)

W sesji poprzedzającej pierwszą lekcję użytkownik sam zbudował i uruchomił end-to-end:
endpointy FastAPI z walidacją Pydantic, rozbicie na routery, monorepo (backend/ + frontend/),
CORS, oraz Client Component w Next.js pobierający dane i renderujący je (koszt wejścia policzony
poprawnie). To nie było samo „przerobienie" — kod działał i został zweryfikowany w przeglądarce.

**Podłoga do dalszej nauki:** rozumie *mechanikę* każdego klocka na poziomie roboczym. Czego
jeszcze NIE sprawdziliśmy dowodowo: czy potrafi ten łańcuch **wyjaśnić spójnie jako całość**
(cel lekcji 01) i czy uzasadni *dlaczego* każdej decyzji pod presją pytań (misja: obrona na rozmowie).

**Implikacje:** nie re-teachować składni Pydantic/routera/CORS. Następne lekcje: albo pogłębienie
jednego przystanku (np. `yield` vs `return` w dependency, preflight OPTIONS), albo skok do warstwy 5
(auth), gdzie te klocki wracają w nowym kontekście.
