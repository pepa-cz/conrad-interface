Instalace a spusteni kontejneru
===============================

  apt-get update
  apt-get install git docker-compose python3-zmq
  nainstalovat docker - https://docs.docker.com/install/linux/docker-ce/debian/
  git clone https://github.com/pepa-cz/conrad-interface.git
  cd conrad-interface
  # Strcit conrad dongle do USB
  docker-compose up

* Ve druhem terminalu

  python3 test/event_loop.py

* Ve tretim terminalu

  python3 test/pair.py
  python3 test/unpair.py
  python3 test/status.py

Testovani
=========

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

