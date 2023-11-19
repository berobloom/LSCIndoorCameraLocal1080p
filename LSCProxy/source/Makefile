
CLIENT_SRC += ./AVAPIs_Client.c
TUTK="tutk_client"

all:
	$(CC) -g $(CFLAGS) -O2 -Wall $(CLIENT_SRC) -I./include -L/usr/lib -lIOTCAPIs -lAVAPIs -lpthread -o $(TUTK)

clean:
	rm -rf *.o *~ $(TUTK)
