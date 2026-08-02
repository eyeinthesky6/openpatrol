// OpenPatrol Rev-A reference safety/motor controller
// Apache-2.0 software; hardware safety remains in the normally-closed relay loop.
#include <Arduino.h>

// Verify every pin against the selected RP2040/ESP32-S3 board before power-up.
static const uint8_t LF_A=2, LF_B=3, LR_A=4, LR_B=5;
static const uint8_t RF_A=6, RF_B=7, RR_A=8, RR_B=9;
static const uint8_t LEFT_PWM=10, RIGHT_PWM=11, LEFT_DIR=12, RIGHT_DIR=13;
static const uint8_t DRIVER_ENABLE=14, SAFETY_LOOP_OK=15, ESTOP_OK=16;
static const uint8_t DRIVER_FAULT=17, CHARGER_PRESENT=18, MAST_RETRACTED_OK=19;
static const uint8_t DRIVE_MOVING_OUTPUT=20, BATTERY_ADC=A0;

static const uint32_t BAUD=115200;
static const uint32_t COMMAND_TIMEOUT_MS=200;
static const uint32_t CONTROL_PERIOD_MS=20;
static const uint32_t STATUS_PERIOD_MS=50;
static const float WHEEL_DIAMETER_MM=100.0f;
static const int32_t COUNTS_PER_WHEEL_REV=1320; // MEASURE and replace.
static const float MAX_WHEEL_MM_S=500.0f;
static const float MAX_WHEEL_MM_S_MAST_EXTENDED=180.0f;
static const float KP=0.30f;                  // Conservative starting value; tune wheels-up.
static const float KI=0.015f;
static const float FEEDFORWARD_PWM_PER_MM_S=0.38f;
static const float BATTERY_MV_PER_ADC_COUNT=15.80f; // Calibrate with a meter.

volatile int32_t lfTicks=0, lrTicks=0, rfTicks=0, rrTicks=0;
int32_t lastLeftTicks=0, lastRightTicks=0;
float targetLeft=0, targetRight=0, leftIntegral=0, rightIntegral=0;
uint32_t lastCommandMs=0, lastControlMs=0, lastStatusMs=0, lastSequence=0;
bool commandEnabled=false;
char lineBuffer[128]; size_t lineLength=0;

uint16_t crc16(const uint8_t* data, size_t length){
  uint16_t crc=0xFFFF;
  for(size_t i=0;i<length;i++){
    crc^=(uint16_t)data[i]<<8;
    for(uint8_t bit=0;bit<8;bit++) crc=(crc&0x8000)?(uint16_t)((crc<<1)^0x1021):(uint16_t)(crc<<1);
  }
  return crc;
}
void lfISR(){ lfTicks += digitalRead(LF_B) ? -1 : 1; }
void lrISR(){ lrTicks += digitalRead(LR_B) ? -1 : 1; }
void rfISR(){ rfTicks += digitalRead(RF_B) ? 1 : -1; }
void rrISR(){ rrTicks += digitalRead(RR_B) ? 1 : -1; }

bool safetyLoopOk(){ return digitalRead(SAFETY_LOOP_OK)==LOW; } // isolated NC-loop feedback pulls low when healthy
bool estopOk(){ return digitalRead(ESTOP_OK)==LOW; }
bool driverFaulted(){ return digitalRead(DRIVER_FAULT)==LOW; }
bool chargerConnected(){ return digitalRead(CHARGER_PRESENT)==LOW; }
// Protocol bit 5 remains named MAST_EXTENDED for compatibility. The electrical
// boundary is fail-safe: LOW means confirmed retracted; HIGH/open means extended
// or unknown. Non-mast platforms must fit the documented supervised ground jumper.
bool mastExtended(){ return digitalRead(MAST_RETRACTED_OK)==HIGH; }
float activeWheelLimit(){ return mastExtended()?MAX_WHEEL_MM_S_MAST_EXTENDED:MAX_WHEEL_MM_S; }

void stopDrive(){
  analogWrite(LEFT_PWM,0); analogWrite(RIGHT_PWM,0); digitalWrite(DRIVER_ENABLE,LOW);
  digitalWrite(DRIVE_MOVING_OUTPUT,HIGH); // active-low interlock output to Sentinel mast controller
  leftIntegral=0; rightIntegral=0;
}
void setChannel(uint8_t pwmPin,uint8_t dirPin,float pwm){
  bool forward=pwm>=0; int magnitude=(int)min(255.0f,max(0.0f,abs(pwm)));
  digitalWrite(dirPin,forward?HIGH:LOW); analogWrite(pwmPin,magnitude);
}
int32_t atomicAverage(volatile int32_t& a, volatile int32_t& b){
  noInterrupts(); int32_t av=a,bv=b; interrupts(); return (av+bv)/2;
}

bool parseCommand(char* line){
  if(line[0]!='$') return false;
  char* star=strrchr(line,'*'); if(!star || strlen(star+1)!=4) return false;
  *star='\0'; uint16_t claimed=(uint16_t)strtoul(star+1,nullptr,16);
  const char* payload=line+1; if(crc16((const uint8_t*)payload,strlen(payload))!=claimed) return false;
  char kind=0; unsigned long seq=0; long left=0,right=0; int enabled=0;
  if(sscanf(payload,"%c,%lu,%ld,%ld,%d",&kind,&seq,&left,&right,&enabled)!=5 || kind!='C') return false;
  if(left<-2000 || left>2000 || right<-2000 || right>2000 || (enabled!=0 && enabled!=1)) return false;
  float limit=activeWheelLimit();
  lastSequence=(uint32_t)seq;
  targetLeft=max(-limit,min(limit,(float)left)); targetRight=max(-limit,min(limit,(float)right));
  commandEnabled=enabled==1; lastCommandMs=millis(); return true;
}
void readSerial(){
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\n'){
      lineBuffer[lineLength]='\0'; parseCommand(lineBuffer); lineLength=0;
    } else if(c!='\r'){
      if(lineLength<sizeof(lineBuffer)-1) lineBuffer[lineLength++]=c; else lineLength=0;
    }
  }
}
void controlStep(){
  uint32_t now=millis(); if(now-lastControlMs<CONTROL_PERIOD_MS) return; lastControlMs=now;
  bool timedOut=now-lastCommandMs>COMMAND_TIMEOUT_MS;
  bool safe=safetyLoopOk() && estopOk() && !driverFaulted() && !chargerConnected() && !timedOut && commandEnabled;
  if(!safe){ stopDrive(); return; }
  float limit=activeWheelLimit(); targetLeft=max(-limit,min(limit,targetLeft)); targetRight=max(-limit,min(limit,targetRight));
  int32_t left=atomicAverage(lfTicks,lrTicks), right=atomicAverage(rfTicks,rrTicks);
  int32_t dl=left-lastLeftTicks, dr=right-lastRightTicks; lastLeftTicks=left; lastRightTicks=right;
  const float mmPerTick=(PI*WHEEL_DIAMETER_MM)/(float)COUNTS_PER_WHEEL_REV;
  float measuredLeft=dl*mmPerTick*1000.0f/CONTROL_PERIOD_MS;
  float measuredRight=dr*mmPerTick*1000.0f/CONTROL_PERIOD_MS;
  float leftError=targetLeft-measuredLeft, rightError=targetRight-measuredRight;
  leftIntegral=max(-4000.0f,min(4000.0f,leftIntegral+leftError)); rightIntegral=max(-4000.0f,min(4000.0f,rightIntegral+rightError));
  float leftPwm=targetLeft*FEEDFORWARD_PWM_PER_MM_S+KP*leftError+KI*leftIntegral;
  float rightPwm=targetRight*FEEDFORWARD_PWM_PER_MM_S+KP*rightError+KI*rightIntegral;
  digitalWrite(DRIVE_MOVING_OUTPUT,(abs(targetLeft)>50.0f || abs(targetRight)>50.0f)?LOW:HIGH);
  digitalWrite(DRIVER_ENABLE,HIGH); setChannel(LEFT_PWM,LEFT_DIR,leftPwm); setChannel(RIGHT_PWM,RIGHT_DIR,rightPwm);
}
void sendStatus(){
  uint32_t now=millis(); if(now-lastStatusMs<STATUS_PERIOD_MS) return; lastStatusMs=now;
  uint16_t flags=0; if(!estopOk()) flags|=1; if(!safetyLoopOk()) flags|=2; if(now-lastCommandMs>COMMAND_TIMEOUT_MS) flags|=4; if(driverFaulted()) flags|=8; if(chargerConnected()) flags|=16; if(mastExtended()) flags|=32;
  int32_t left=atomicAverage(lfTicks,lrTicks), right=atomicAverage(rfTicks,rrTicks);
  uint32_t batteryMv=(uint32_t)(analogRead(BATTERY_ADC)*BATTERY_MV_PER_ADC_COUNT);
  char payload[96]; snprintf(payload,sizeof(payload),"S,%lu,%ld,%ld,%lu,%u",(unsigned long)lastSequence,(long)left,(long)right,(unsigned long)batteryMv,(unsigned)flags);
  Serial.print('$'); Serial.print(payload); Serial.print('*'); char crcText[5]; snprintf(crcText,sizeof(crcText),"%04X",crc16((const uint8_t*)payload,strlen(payload))); Serial.println(crcText);
}
void setup(){
  Serial.begin(BAUD);
  pinMode(LF_A,INPUT_PULLUP); pinMode(LF_B,INPUT_PULLUP); pinMode(LR_A,INPUT_PULLUP); pinMode(LR_B,INPUT_PULLUP); pinMode(RF_A,INPUT_PULLUP); pinMode(RF_B,INPUT_PULLUP); pinMode(RR_A,INPUT_PULLUP); pinMode(RR_B,INPUT_PULLUP);
  pinMode(LEFT_PWM,OUTPUT); pinMode(RIGHT_PWM,OUTPUT); pinMode(LEFT_DIR,OUTPUT); pinMode(RIGHT_DIR,OUTPUT); pinMode(DRIVER_ENABLE,OUTPUT); pinMode(DRIVE_MOVING_OUTPUT,OUTPUT);
  pinMode(SAFETY_LOOP_OK,INPUT_PULLUP); pinMode(ESTOP_OK,INPUT_PULLUP); pinMode(DRIVER_FAULT,INPUT_PULLUP); pinMode(CHARGER_PRESENT,INPUT_PULLUP); pinMode(MAST_RETRACTED_OK,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(LF_A),lfISR,CHANGE); attachInterrupt(digitalPinToInterrupt(LR_A),lrISR,CHANGE); attachInterrupt(digitalPinToInterrupt(RF_A),rfISR,CHANGE); attachInterrupt(digitalPinToInterrupt(RR_A),rrISR,CHANGE);
  stopDrive(); lastCommandMs=millis();
}
void loop(){ readSerial(); controlStep(); sendStatus(); }
