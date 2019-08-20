Testovani
=========

Spusteni kontejneru, plne nabehnuti chvili trva..

  docker-compose up  # pripadne 'docker-compose -d up' pro spusteni na pozadi

Pro ucely ladeni, telnet na fhem

  telnet localhost 7072

Testy

  python3 test/pair.py  # Spusteni parovani. Parametr tout urcuje jak dlouho zustane v parovacim rezimu.
  python3 test/unpair.py  # Odparovani zarizeni. Parametr 'device' urcuje zarizeni (klic 'dev' ve statusu)
  python3 test/status.py  # Seznam zarizeni s doplnujicimi informacemi.

Events
======

Asynchronni udalosti prichazejici pres ZMQ (viz example eventloop).

- message - prijata zprava
    - channels - submoduly zarizeni
    - dev - seriove cislo zarizeni
    - raw - RAW prijata zprava
    - rssi - odstup signal/sum
    - type - typ zarizeni

- prot_state
    - CMDs_done - nedoslo k zadnym chybam
    - CMDs_done_Error: xx - pri poslednim prenosu doslo k chybe xx
    - CMDs_pending: zpravy cekajici na odeslani
    - CMDs_processing... - zpracovavani pozadavku
    - Info cleared: statistiky protokolu byly vyresetovany
    - null - zadne informace

- rcv_cnt - prijata zprava

- snd_cnt - odeslana zprava

- resnd_cnt - retransmit
