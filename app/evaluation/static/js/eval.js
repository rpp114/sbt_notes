
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