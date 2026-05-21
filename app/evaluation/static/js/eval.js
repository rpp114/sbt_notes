
function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }
    }, 1000);
}

// window.onload = function () {
//     var fiveMinutes = 60 * 5,
//         display = document.querySelector('#time');
//     startTimer(fiveMinutes, display);
// };


function updateReport(e) {
    var id = e.id.split('_')[0];
    
    document.getElementById(id).textContent = e.value;

    // var section_text = document.getElementById('report_text').textContent

}

// To Find the <p> tags in the report text:

// re.findall(r'<p id="(.*?)">',x)
// ['things', 'stuff']

function showModal() {

    var modal = document.getElementById('popup');

    modal.classList.add('is-active');

}

function closeModal() {

    var modal = document.getElementById('popup');

    modal.classList.remove('is-active');

}


function sendReportSections() {
    var url = window.location.href;

    var sections = document.getElementsByClassName('report_section');

    var report = {}, section_name;

    for (j in sections) {
        section_name = sections[j].id;

        report[section_name] = sections[j].innerText;

    };


    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(report));

    console.log('HELLO')
    console.log(xhr.response);
    console.log(xhr.responseType);


}



// Auto save- draft report: 

function autoSaveReport() {

    const form = document.getElementById("report_form");

    let saveTimeout = null;
    let lastSavedData = "";
    let isSaving = false;

    // Serialize form data
    function getFormData() {
        const data = new FormData(form);
        console.log(data)
        return new URLSearchParams(data).toString();
    }

    // Actual save function
    async function saveDraft() {
        if (isSaving) return;
        const currentData = getFormData();

        // nothing changed → skip save
        if (currentData === lastSavedData) return;

        isSaving = true;

        try {
            const res = await fetch(form.action, {
                method: form.method,
                body: new FormData(form)
            });

            if (res.ok) {
                lastSavedData = currentData;
            }
        } finally {
            isSaving = false;
        }
    }

    // Debounce: wait until user stops typing
    function scheduleSave() {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveDraft, 1500); // 1.5s after last keystroke
    }

    // Listen for changes
    form.addEventListener("input", scheduleSave);

    // Optional: periodic backup in case typing stops unexpectedly
    setInterval(saveDraft, 30000); // every 30s safety net


}