
const statusCircle = document.getElementById('status');
const locBtn = document.getElementById('locBtn');
const locInfo = document.getElementById('locInfo');
const photoInput = document.getElementById('photoInput');
const damageTypeDiv = document.getElementById('damageTypeDiv');
const damageTypeSelect = document.getElementById('damageType');
const submitBtn = document.getElementById('submitBtn');
const log = document.getElementById('log');

let position = null;
let photoFile = null;

function logMsg(msg){ log.textContent += msg + "\n"; }

locBtn.addEventListener('click', () => {
    statusCircle.style.background = '#f00';
    logMsg('Requesting location...');
    const watchId = navigator.geolocation.watchPosition(
        (pos) => {
            position = pos;
            locInfo.textContent = `Lat: ${pos.coords.latitude.toFixed(6)}, Lon: ${pos.coords.longitude.toFixed(6)}, Acc: ${pos.coords.accuracy.toFixed(1)} m`;
            if (pos.coords.accuracy <= 5){
                statusCircle.style.background = '#0f0';
                navigator.geolocation.clearWatch(watchId);
                // show photo input
                photoInput.style.display = 'block';
            }else{
                statusCircle.style.background = '#ff0';
            }
        },
        (err) => {
            logMsg('Error getting location: ' + err.message);
            statusCircle.style.background = '#ccc';
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
});

photoInput.addEventListener('change', (e) => {
    photoFile = e.target.files[0];
    if(photoFile){
        damageTypeDiv.style.display = 'block';
    }
});

submitBtn.addEventListener('click', async () => {
    if(!position || !photoFile){
        alert('Missing location or photo');
        return;
    }
    const fd = new FormData();
    fd.append('latitude', position.coords.latitude);
    fd.append('longitude', position.coords.longitude);
    fd.append('accuracy', position.coords.accuracy);
    fd.append('damage_type', damageTypeSelect.value);
    fd.append('photo', photoFile, photoFile.name);

    try{
        const res = await fetch('/api/incident', {method:'POST', body: fd});
        if(res.ok){
            logMsg('Report submitted!');
            // reset
            damageTypeDiv.style.display = 'none';
            photoInput.style.display = 'none';
            locInfo.textContent = '';
            statusCircle.style.background = '#ccc';
            photoInput.value = '';
            position = null; photoFile = null;
        }else{
            const err = await res.json();
            logMsg('Server error: ' + err.detail);
        }
    }catch(e){
        logMsg('Network error: ' + e.message);
    }
});
