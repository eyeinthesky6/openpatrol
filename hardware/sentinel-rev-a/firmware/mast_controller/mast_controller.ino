// OpenPatrol Sentinel Rev-A mast controller
// Apache-2.0 software. Upper/lower limits and tilt remain hardwired to actuator enable.
#include <Arduino.h>

// Verify pins and active levels against the selected RP2040 board and isolator board.
static const uint8_t ACTUATOR_PWM=2, ACTUATOR_DIR=3, ACTUATOR_ENABLE=4;
static const uint8_t LOWER_LIMIT_OK=5, UPPER_LIMIT_OK=6, TILT_OK=7;
static const uint8_t DRIVE_MOVING=8, ACTUATOR_FAULT=9, RETRACTED_OK_OUTPUT=10;
static const uint8_t HEIGHT_ADC=A0;
static const uint32_t BAUD=115200;
static const uint32_t COMMAND_TIMEOUT_MS=500;
static const uint32_t CONTROL_PERIOD_MS=20;
static const uint32_t STATUS_PERIOD_MS=50;
static const int MIN_HEIGHT_MM=980, MAX_HEIGHT_MM=1500, EXTENDED_THRESHOLD_MM=1120;
static const int HEIGHT_ADC_AT_MIN=140, HEIGHT_ADC_AT_MAX=890; // MEASURE on the assembled mast.
static const int HEIGHT_ADC_MARGIN=60;
static const int POSITION_DEADBAND_MM=6;
static const int ACTUATOR_PWM_VALUE=180;

uint32_t lastCommandMs=0,lastControlMs=0,lastStatusMs=0,lastSequence=0;
int targetHeightMm=MIN_HEIGHT_MM;
bool commandEnabled=false;
char lineBuffer[128]; size_t lineLength=0;

uint16_t crc16(const uint8_t* data,size_t length){
  uint16_t crc=0xFFFF;
  for(size_t i=0;i<length;i++){
    crc^=(uint16_t)data[i]<<8;
    for(uint8_t bit=0;bit<8;bit++) crc=(crc&0x8000)?(uint16_t)((crc<<1)^0x1021):(uint16_t)(crc<<1);
  }
  return crc;
}
bool lowerLimitOk(){return digitalRead(LOWER_LIMIT_OK)==LOW;}
bool upperLimitOk(){return digitalRead(UPPER_LIMIT_OK)==LOW;}
bool tiltOk(){return digitalRead(TILT_OK)==LOW;}
bool driveMoving(){return digitalRead(DRIVE_MOVING)==LOW;}
bool actuatorFaulted(){return digitalRead(ACTUATOR_FAULT)==LOW;}
int heightRaw(){return analogRead(HEIGHT_ADC);}
bool heightSensorValid(int raw){
  return raw>=HEIGHT_ADC_AT_MIN-HEIGHT_ADC_MARGIN && raw<=HEIGHT_ADC_AT_MAX+HEIGHT_ADC_MARGIN;
}
int heightMmFromRaw(int raw){
  long value=map(raw,HEIGHT_ADC_AT_MIN,HEIGHT_ADC_AT_MAX,MIN_HEIGHT_MM,MAX_HEIGHT_MM);
  return constrain((int)value,MIN_HEIGHT_MM,MAX_HEIGHT_MM);
}
void publishRetractedOk(int current,bool sensorValid){
  // Active-low fail-safe confirmation. High/open means extended OR unknown.
  bool confirmedRetracted=sensorValid && current<EXTENDED_THRESHOLD_MM;
  digitalWrite(RETRACTED_OK_OUTPUT,confirmedRetracted?LOW:HIGH);
}
void stopMast(){analogWrite(ACTUATOR_PWM,0);digitalWrite(ACTUATOR_ENABLE,LOW);}
void driveMast(bool up){
  digitalWrite(ACTUATOR_DIR,up?HIGH:LOW);
  digitalWrite(ACTUATOR_ENABLE,HIGH);
  analogWrite(ACTUATOR_PWM,ACTUATOR_PWM_VALUE);
}
bool parseCommand(char* line){
  if(line[0]!='$') return false;
  char* star=strrchr(line,'*'); if(!star || strlen(star+1)!=4) return false;
  *star='\0'; uint16_t claimed=(uint16_t)strtoul(star+1,nullptr,16);
  const char* payload=line+1; if(crc16((const uint8_t*)payload,strlen(payload))!=claimed) return false;
  char kind=0; unsigned long seq=0; long target=0; int enabled=0;
  if(sscanf(payload,"%c,%lu,%ld,%d",&kind,&seq,&target,&enabled)!=4 || kind!='M') return false;
  if(target<MIN_HEIGHT_MM || target>MAX_HEIGHT_MM || (enabled!=0 && enabled!=1)) return false;
  lastSequence=(uint32_t)seq; targetHeightMm=(int)target; commandEnabled=enabled==1; lastCommandMs=millis(); return true;
}
void readSerial(){
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\n'){lineBuffer[lineLength]='\0';parseCommand(lineBuffer);lineLength=0;}
    else if(c!='\r'){if(lineLength<sizeof(lineBuffer)-1) lineBuffer[lineLength++]=c;else lineLength=0;}
  }
}
void controlStep(){
  uint32_t now=millis(); if(now-lastControlMs<CONTROL_PERIOD_MS) return; lastControlMs=now;
  int raw=heightRaw(); bool sensorValid=heightSensorValid(raw); int current=heightMmFromRaw(raw);
  bool timedOut=now-lastCommandMs>COMMAND_TIMEOUT_MS;
  bool safe=commandEnabled && !timedOut && tiltOk() && !driveMoving() && !actuatorFaulted() && sensorValid;
  if(!safe){stopMast();publishRetractedOk(current,sensorValid);return;}
  int error=targetHeightMm-current;
  if(abs(error)<=POSITION_DEADBAND_MM){stopMast();}
  else if(error>0){if(upperLimitOk()) driveMast(true); else stopMast();}
  else {if(lowerLimitOk()) driveMast(false); else stopMast();}
  publishRetractedOk(current,sensorValid);
}
void sendStatus(){
  uint32_t now=millis(); if(now-lastStatusMs<STATUS_PERIOD_MS) return; lastStatusMs=now;
  int raw=heightRaw(); bool sensorValid=heightSensorValid(raw); int current=heightMmFromRaw(raw);
  uint16_t flags=0;
  if(!lowerLimitOk()) flags|=1; if(!upperLimitOk()) flags|=2;
  if(now-lastCommandMs>COMMAND_TIMEOUT_MS) flags|=4; if(!tiltOk()) flags|=8;
  if(actuatorFaulted()) flags|=16; if(driveMoving()) flags|=32; if(current>=EXTENDED_THRESHOLD_MM) flags|=64;
  if(!sensorValid) flags|=128;
  char payload[80]; snprintf(payload,sizeof(payload),"T,%lu,%d,%u",(unsigned long)lastSequence,current,(unsigned)flags);
  Serial.print('$');Serial.print(payload);Serial.print('*');char crcText[5];snprintf(crcText,sizeof(crcText),"%04X",crc16((const uint8_t*)payload,strlen(payload)));Serial.println(crcText);
}
void setup(){
  Serial.begin(BAUD);
  pinMode(ACTUATOR_PWM,OUTPUT);pinMode(ACTUATOR_DIR,OUTPUT);pinMode(ACTUATOR_ENABLE,OUTPUT);
  pinMode(LOWER_LIMIT_OK,INPUT_PULLUP);pinMode(UPPER_LIMIT_OK,INPUT_PULLUP);pinMode(TILT_OK,INPUT_PULLUP);
  pinMode(DRIVE_MOVING,INPUT_PULLUP);pinMode(ACTUATOR_FAULT,INPUT_PULLUP);pinMode(RETRACTED_OK_OUTPUT,OUTPUT);
  stopMast();digitalWrite(RETRACTED_OK_OUTPUT,HIGH);lastCommandMs=millis();
}
void loop(){readSerial();controlStep();sendStatus();}
