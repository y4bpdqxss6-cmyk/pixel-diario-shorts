import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Fa mayor, marimba (seno + 4.º armónico con caída rápida) + bajo pulsado + clic de madera, 116 bpm
# (antes: piano suave + colchón cálido + hi-hat, Re mayor 100 bpm)
bpm=116; step=60/bpm/2
prog=[[53,60,65,69],[50,57,62,65],[46,53,58,62],[48,55,60,64]]
pat=[0,3,2,3,1,3,2,3]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    if k%8 in (0,2,3,5,6):
        e=min(s+int(0.5*sr),len(t)); tt=t[s:e]-t[s]; fr=f(ch[pat[k%8]]+12)
        out[s:e]+=0.06*(np.sin(2*np.pi*fr*tt)*np.exp(-tt*7)+0.3*np.sin(2*np.pi*fr*4*tt)*np.exp(-tt*30))
    if k%4==0:
        e=min(s+int(0.35*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.09*np.sin(2*np.pi*f(ch[0]-12)*tt)*np.exp(-tt*6)
    if k%2==1:
        e=min(s+int(0.03*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.03*np.sin(2*np.pi*1800*tt)*np.exp(-tt*150)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.35
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
