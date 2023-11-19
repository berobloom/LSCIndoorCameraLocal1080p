#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <fcntl.h>
#include "IOTCAPIs.h"
#include "AVAPIs.h"
#include "AVFRAMEINFO.h"
#include "AVIOCTRLDEFs.h"
#include <signal.h>

#define AUDIO_BUF_SIZE	1024

#define VIDEO_BUF_SIZE	128000

#define AUDIO_FIFO_PATH "audio_fifo"
#define VIDEO_FIFO_PATH "video_fifo"


// *** AV server ID and password, set here ***
char avID[]="admin";
char avPass[]="123456";
int gSleepUs = 10000;

int graceful_shutdown = 0;
int sigkill = 0;

void sigpipe_handler(int signo) 
{
    if (signo == SIGPIPE) 
	{
    	fprintf(stderr, "Caught SIGPIPE signal\n");
	}
	else if (signo == SIGINT) 
	{
		if (sigkill != 1)
		{
			fprintf(stderr, "Caught SIGINT signal\n. Gracefully shutting down...\n");
			graceful_shutdown = 1;
			sigkill = 1;
		}
		else
		{
			fprintf(stderr, "Caught 2 SIGINT signals\n. Forcefully shutting down...\n");
			exit(1);
		}
    }
}

void PrintErrHandling (int nErr)
{
	switch (nErr)
	{
	case IOTC_ER_SERVER_NOT_RESPONSE :
		//-1 IOTC_ER_SERVER_NOT_RESPONSE
		printf ("[Error code : %d]\n", IOTC_ER_SERVER_NOT_RESPONSE );
		printf ("Master doesn't respond.\n");
		printf ("Please check the network wheather it could connect to the Internet.\n");
		break;
	case IOTC_ER_FAIL_RESOLVE_HOSTNAME :
		//-2 IOTC_ER_FAIL_RESOLVE_HOSTNAME
		printf ("[Error code : %d]\n", IOTC_ER_FAIL_RESOLVE_HOSTNAME);
		printf ("Can't resolve hostname.\n");
		break;
	case IOTC_ER_ALREADY_INITIALIZED :
		//-3 IOTC_ER_ALREADY_INITIALIZED
		printf ("[Error code : %d]\n", IOTC_ER_ALREADY_INITIALIZED);
		printf ("Already initialized.\n");
		break;
	case IOTC_ER_FAIL_CREATE_MUTEX :
		//-4 IOTC_ER_FAIL_CREATE_MUTEX
		printf ("[Error code : %d]\n", IOTC_ER_FAIL_CREATE_MUTEX);
		printf ("Can't create mutex.\n");
		break;
	case IOTC_ER_FAIL_CREATE_THREAD :
		//-5 IOTC_ER_FAIL_CREATE_THREAD
		printf ("[Error code : %d]\n", IOTC_ER_FAIL_CREATE_THREAD);
		printf ("Can't create thread.\n");
		break;
	case IOTC_ER_UNLICENSE :
		//-10 IOTC_ER_UNLICENSE
		printf ("[Error code : %d]\n", IOTC_ER_UNLICENSE);
		printf ("This UID is unlicense.\n");
		printf ("Check your UID.\n");
		break;
	case IOTC_ER_NOT_INITIALIZED :
		//-12 IOTC_ER_NOT_INITIALIZED
		printf ("[Error code : %d]\n", IOTC_ER_NOT_INITIALIZED);
		printf ("Please initialize the IOTCAPI first.\n");
		break;
	case IOTC_ER_TIMEOUT :
		//-13 IOTC_ER_TIMEOUT
		break;
	case IOTC_ER_INVALID_SID :
		//-14 IOTC_ER_INVALID_SID
		printf ("[Error code : %d]\n", IOTC_ER_INVALID_SID);
		printf ("This SID is invalid.\n");
		printf ("Please check it again.\n");
		break;
	case IOTC_ER_EXCEED_MAX_SESSION :
		//-18 IOTC_ER_EXCEED_MAX_SESSION
		printf ("[Error code : %d]\n", IOTC_ER_EXCEED_MAX_SESSION);
		printf ("[Warning]\n");
		printf ("The amount of session reach to the maximum.\n");
		printf ("It cannot be connected unless the session is released.\n");
		break;
	case IOTC_ER_CAN_NOT_FIND_DEVICE :
		//-19 IOTC_ER_CAN_NOT_FIND_DEVICE
		printf ("[Error code : %d]\n", IOTC_ER_CAN_NOT_FIND_DEVICE);
		printf ("Device didn't register on server, so we can't find device.\n");
		printf ("Please check the device again.\n");
		printf ("Retry...\n");
		break;
	case IOTC_ER_SESSION_CLOSE_BY_REMOTE :
		//-22 IOTC_ER_SESSION_CLOSE_BY_REMOTE
		printf ("[Error code : %d]\n", IOTC_ER_SESSION_CLOSE_BY_REMOTE);
		printf ("Session is closed by remote so we can't access.\n");
		printf ("Please close it or establish session again.\n");
		break;
	case IOTC_ER_REMOTE_TIMEOUT_DISCONNECT :
		//-23 IOTC_ER_REMOTE_TIMEOUT_DISCONNECT
		printf ("[Error code : %d]\n", IOTC_ER_REMOTE_TIMEOUT_DISCONNECT);
		printf ("We can't receive an acknowledgement character within a TIMEOUT.\n");
		printf ("It might that the session is disconnected by remote.\n");
		printf ("Please check the network wheather it is busy or not.\n");
		printf ("And check the device and user equipment work well.\n");
		break;
	case IOTC_ER_DEVICE_NOT_LISTENING :
		//-24 IOTC_ER_DEVICE_NOT_LISTENING
		printf ("[Error code : %d]\n", IOTC_ER_DEVICE_NOT_LISTENING);
		printf ("Device doesn't listen or the sessions of device reach to maximum.\n");
		printf ("Please release the session and check the device wheather it listen or not.\n");
		break;
	case IOTC_ER_CH_NOT_ON :
		//-26 IOTC_ER_CH_NOT_ON
		printf ("[Error code : %d]\n", IOTC_ER_CH_NOT_ON);
		printf ("Channel isn't on.\n");
		printf ("Please open it by IOTC_Session_Channel_ON() or IOTC_Session_Get_Free_Channel()\n");
		printf ("Retry...\n");
		break;
	case IOTC_ER_SESSION_NO_FREE_CHANNEL :
		//-31 IOTC_ER_SESSION_NO_FREE_CHANNEL
		printf ("[Error code : %d]\n", IOTC_ER_SESSION_NO_FREE_CHANNEL);
		printf ("All channels are occupied.\n");
		printf ("Please release some channel.\n");
		break;
	case IOTC_ER_TCP_TRAVEL_FAILED :
		//-32 IOTC_ER_TCP_TRAVEL_FAILED
		printf ("[Error code : %d]\n", IOTC_ER_TCP_TRAVEL_FAILED);
		printf ("Device can't connect to Master.\n");
		printf ("Don't let device use proxy.\n");
		printf ("Close firewall of device.\n");
		printf ("Or open device's TCP port 80, 443, 8080, 8000, 21047.\n");
		break;
	case IOTC_ER_TCP_CONNECT_TO_SERVER_FAILED :
		//-33 IOTC_ER_TCP_CONNECT_TO_SERVER_FAILED
		printf ("[Error code : %d]\n", IOTC_ER_TCP_CONNECT_TO_SERVER_FAILED);
		printf ("Device can't connect to server by TCP.\n");
		printf ("Don't let server use proxy.\n");
		printf ("Close firewall of server.\n");
		printf ("Or open server's TCP port 80, 443, 8080, 8000, 21047.\n");
		printf ("Retry...\n");
		break;
	case IOTC_ER_NO_PERMISSION :
		//-40 IOTC_ER_NO_PERMISSION
		printf ("[Error code : %d]\n", IOTC_ER_NO_PERMISSION);
		printf ("This UID's license doesn't support TCP.\n");
		break;
	case IOTC_ER_NETWORK_UNREACHABLE :
		//-41 IOTC_ER_NETWORK_UNREACHABLE
		printf ("[Error code : %d]\n", IOTC_ER_NETWORK_UNREACHABLE);
		printf ("Network is unreachable.\n");
		printf ("Please check your network.\n");
		printf ("Retry...\n");
		break;
	case IOTC_ER_FAIL_SETUP_RELAY :
		//-42 IOTC_ER_FAIL_SETUP_RELAY
		printf ("[Error code : %d]\n", IOTC_ER_FAIL_SETUP_RELAY);
		printf ("Client can't connect to a device via Lan, P2P, and Relay mode\n");
		break;
	case IOTC_ER_NOT_SUPPORT_RELAY :
		//-43 IOTC_ER_NOT_SUPPORT_RELAY
		printf ("[Error code : %d]\n", IOTC_ER_NOT_SUPPORT_RELAY);
		printf ("Server doesn't support UDP relay mode.\n");
		printf ("So client can't use UDP relay to connect to a device.\n");
		break;

	default :
		break;
	}
}

void *thread_ReceiveAudio(void *arg)
{
	printf("Audio Starting...\n");

	int avIndex = *(int *)arg;
	char buf[AUDIO_BUF_SIZE]={0};

	FRAMEINFO_t frameInfo;
	unsigned int frmNo;
	int ret;
	printf("Start IPCAM audio stream OK!\n");

	int audio_pipe_fd = open(AUDIO_FIFO_PATH, O_WRONLY);
    if (audio_pipe_fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }

	while(1)
	{
		ret = avCheckAudioBuf(avIndex);
		if(ret < 0) 
			break;
		if(ret < 25)
		{
			usleep(gSleepUs);
			continue;
		}
		
		ret = avRecvAudioData(avIndex, buf, AUDIO_BUF_SIZE, (char *)&frameInfo, sizeof(FRAMEINFO_t), &frmNo);

		if(ret == AV_ER_SESSION_CLOSE_BY_REMOTE)
		{
			printf("[thread_ReceiveAudio] AV_ER_SESSION_CLOSE_BY_REMOTE\n");
			break;
		}
		else if(ret == AV_ER_REMOTE_TIMEOUT_DISCONNECT)
		{
			printf("[thread_ReceiveAudio] AV_ER_REMOTE_TIMEOUT_DISCONNECT\n");
			break;
		}
		else if(ret == IOTC_ER_INVALID_SID)
		{
			printf("[thread_ReceiveAudio] Session cant be used anymore\n");
			break;
		}
		else if(ret == AV_ER_LOSED_THIS_FRAME)
		{
			continue;
		}

		if (graceful_shutdown == 1)
		{
			break;
		}

        // Audio Playback
        ret = write(audio_pipe_fd, buf, ret);
        if (ret < 0) {
            printf("audio_playback::write , ret=[%d]\n", ret);
        }

		if (graceful_shutdown == 1)
		{
			break;
		}
	}
	// Close unused pipe ends
	close(audio_pipe_fd);

	printf("[thread_ReceiveAudio] thread exit\n");

	return 0;
}

void *thread_bufferClean()
{
	while (1)
	{
		sleep(60);
		avClientCleanVideoBuf(0);
		sleep(60);
		avClientCleanAudioBuf(0);
	}
}

void *thread_ReceiveVideo(void *arg)
{
	printf("Video starting...\n");
	int avIndex = *(int *)arg;
	char buf[VIDEO_BUF_SIZE]={0};
	int ret;
	
	FRAMEINFO_t frameInfo;
	unsigned int frmNo;
	printf("Start IPCAM video stream OK!\n");

	int video_pipe_fd = open(VIDEO_FIFO_PATH, O_WRONLY);
    if (video_pipe_fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }

	int outBufSize = 0;
	int outFrmSize = 0;
	int outFrmInfoSize = 0;
	
	while(1)
	{
		ret = avRecvFrameData2(avIndex, buf, VIDEO_BUF_SIZE, &outBufSize, &outFrmSize, (char *)&frameInfo, sizeof(FRAMEINFO_t), &outFrmInfoSize, &frmNo);

		if(ret == AV_ER_DATA_NOREADY)
		{	
			usleep(gSleepUs);
			continue;
		}
		else if(ret == AV_ER_SESSION_CLOSE_BY_REMOTE)
		{
			printf("[thread_ReceiveVideo] AV_ER_SESSION_CLOSE_BY_REMOTE\n");
			break;
		}
		else if(ret == AV_ER_REMOTE_TIMEOUT_DISCONNECT)
		{
			printf("[thread_ReceiveVideo] AV_ER_REMOTE_TIMEOUT_DISCONNECT\n");
			break;
		}
		else if(ret == IOTC_ER_INVALID_SID)
		{
			printf("[thread_ReceiveVideo] Session cant be used anymore\n");
			break;
		}

        // Video Playback
        ret = write(video_pipe_fd, buf, ret);
        if (ret < 0) {
            printf("video_playback::write , ret=[%d]\n", ret);
        }

		if (graceful_shutdown == 1)
		{
			break;
		}
	}

	// Close unused pipe ends
	close(video_pipe_fd);

	printf("[thread_ReceiveVideo] thread exit\n");

	return 0;
}

// Send IOCtrl commands to device
int start_ipcam_stream(int avIndex)
{
	int ret;

	// IOCtrl: Turn NightVision Off [Default]
	SMsgAVIoctrlSetVideoModeReq ioNightvision;
	ioNightvision.channel = 1;
	ioNightvision.mode = 1;

	if((ret = avSendIOCtrl(avIndex, 0x5000, (char *)&ioNightvision, sizeof(SMsgAVIoctrlSetVideoModeReq)) < 0))
	{
		printf("start_ipcam_stream failed[%d]\n", ret);
		return 0;
	}

	// IOCtrl: Set video quality to 1080p
	SMsgAVIoctrlSetStreamCtrlReq ioQuality;
	ioQuality.channel = 0;
	ioQuality.quality = 2;

	if((ret = avSendIOCtrl(avIndex, IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ, (char *)&ioQuality, sizeof(SMsgAVIoctrlSetStreamCtrlReq)) < 0))
	{
		printf("start_ipcam_stream failed[%d]\n", ret);
		return 0;
	}

	// IOCtrl: Start the camera
	SMsgAVIoctrlAVStream ioMsg;
	memset(&ioMsg, 0, sizeof(SMsgAVIoctrlAVStream));
	if((ret = avSendIOCtrl(avIndex, IOTYPE_USER_IPCAM_START, (char *)&ioMsg, sizeof(SMsgAVIoctrlAVStream))) < 0)
	{
		printf("start_ipcam_stream failed[%d]\n", ret);
		return 0;
	}

	// IOCtrl: Start audio
	if((ret = avSendIOCtrl(avIndex, IOTYPE_USER_IPCAM_AUDIOSTART, (char *)&ioMsg, sizeof(SMsgAVIoctrlAVStream))) < 0)
	{
		printf("start_ipcam_stream failed[%d]\n", ret);
		return 0;
	}

	return 1;
}

void *thread_ConnectCCR(void *arg)
{
	int ret;
	
	pid_t ffmpeg_pid;
	ffmpeg_pid = fork();
    int audio_pipe_fd = open(AUDIO_FIFO_PATH, O_RDWR);
    if (audio_pipe_fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }

    int video_pipe_fd = open(VIDEO_FIFO_PATH, O_RDWR);
    if (video_pipe_fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }

    if (ffmpeg_pid == 0) {
        execlp(
			"ffmpeg", "ffmpeg", "-re", "-hide_banner", "-thread_queue_size", "4096", "-f", "s16le", "-ar", "8000", "-ac", "1", "-i", AUDIO_FIFO_PATH, 
			"-thread_queue_size", "4096", "-f", "h264", "-i", VIDEO_FIFO_PATH, 
			"-c:a", "aac", "-b:a", "8000", "-c:v", "libx264", "-f", "rtsp", "-rtsp_transport", "tcp", "rtsp://localhost:8554/stream", NULL);
        perror("execlp");
        exit(EXIT_FAILURE);
    } else if (ffmpeg_pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    }
	
	int SID;
	char *UID=(char *)arg;
	int tmpSID = IOTC_Get_SessionID();
	if(tmpSID < 0)
	{
		printf("Get session ID failed\n");
		return 0;
	}

	SID = IOTC_Connect_ByUID_Parallel(UID, tmpSID);
	if(SID < 0)
	{
		printf("Connect by UID failed\n");
		return 0;
	}

	int nResend=-1;
	unsigned int srvType;
	int avIndex = avClientStart2(SID, avID, avPass, 20, &srvType, 0, &nResend);
	if(avIndex < 0)
	{
		printf("avClientStart2 failed[%d]\n", avIndex);
		return 0;
	}

	printf("Client started!\n");


	if(start_ipcam_stream(avIndex))
	{
		pthread_t ThreadVideo_ID = 0, ThreadAudio_ID = 0, ThreadBufferClean_ID = 0;
		
		printf("Start IP Camera...\n");
		
		// Create video thread
		if ( (ret=pthread_create(&ThreadVideo_ID, NULL, &thread_ReceiveVideo, (void *)&avIndex)) )
		{
			printf("Create Video Receive thread failed\n");
			exit(-1);
		}

		// Create audio thread
		if ( (ret=pthread_create(&ThreadAudio_ID, NULL, &thread_ReceiveAudio, (void *)&avIndex)) )
		{
			printf("Create Audio Receive thread failed\n");
			exit(-1);
		}

		// Create bufferclean thread
		if ((ret = pthread_create(&ThreadBufferClean_ID, NULL, &thread_bufferClean, NULL))) {
			printf("Create Audio Receive thread failed\n");
			exit(-1);
		}

		if( ThreadVideo_ID!=0)
			pthread_join(ThreadVideo_ID, NULL);
		if( ThreadAudio_ID!=0)
			pthread_join(ThreadAudio_ID, NULL);
	}

	// IOCtrl: Stop the camera
	SMsgAVIoctrlAVStream ioMsg;
	memset(&ioMsg, 0, sizeof(SMsgAVIoctrlAVStream));
	if((ret = avSendIOCtrl(avIndex, IOTYPE_USER_IPCAM_STOP, (char *)&ioMsg, sizeof(SMsgAVIoctrlAVStream))) < 0)
	{
		printf("stop_ipcam_audio failed[%d]\n", ret);
		return 0;
	}

	// Close unused pipe ends
	close(video_pipe_fd);
	close(audio_pipe_fd);
	
	kill(ffmpeg_pid, SIGKILL);
	
	avClientExit(SID, 0);
	avClientStop(avIndex);
	printf("Client stopped\n");
	IOTC_Session_Close(SID);
	printf("Session closed\n");

	return NULL;
}

int main(int argc, char *argv[])
{
	signal(SIGPIPE, sigpipe_handler);
	signal(SIGINT, sigpipe_handler);
	srand(time(NULL));

	int ret;

	if(argc < 2)
	{
		printf("Argument Error!!!\n");
		printf("Usage: ./AVAPIs_Client UID\n");
		return -1;
	}

	char *UID = argv[1];

	ret = IOTC_Initialize2(0);
	if(ret != IOTC_ER_NoERROR)
	{
		printf("IOTCAPIs_Device exit...!!\n");
		PrintErrHandling (ret);
		return 0;
	}

	avInitialize(32);

	// Retrieve AVAPI Version
	int avVer = avGetAVApiVer();
	unsigned char *p = (unsigned char *)&avVer;
	char szAVVer[16];
	sprintf(szAVVer, "%d.%d.%d.%d", p[3], p[2], p[1], p[0]);

	// Run the application
	printf("LSC Indoor Camera Proxy[1.0] AVAPI version[%s]\n", szAVVer);  

	// Search for the camera on the local network
	int i;
	struct st_LanSearchInfo *psLanSearchInfo = (struct st_LanSearchInfo *)malloc(sizeof(struct st_LanSearchInfo)*12);
	if(psLanSearchInfo != NULL)
	{
		// wait time 1000 ms to get result, if result is 0 you can extend to 2000 ms
		int nDeviceNum = IOTC_Lan_Search(psLanSearchInfo, 12, 1000);
		printf("Searching lan for camera's...\n");
		for(i=0;i<nDeviceNum;i++)
		{
			printf("UID[%s] Addr[%s:%d]\n", psLanSearchInfo[i].UID, psLanSearchInfo[i].IP, psLanSearchInfo[i].port);
		}
		free(psLanSearchInfo);
	}
	printf("LAN search done...\n");

	// Create the connection thread
	pthread_t ConnectThread_ID;
	if((ret = pthread_create(&ConnectThread_ID, NULL, &thread_ConnectCCR, (void *)UID)))
	{
		printf("pthread_create(ConnectThread_ID), ret=[%d]\n", ret);
		exit(-1);
	}
	pthread_join(ConnectThread_ID, NULL);

	avDeInitialize();
	IOTC_DeInitialize();

	return 0;
}


