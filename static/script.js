let chart1, chart2;

async function analisar(dadosManual=null) {

    let dados;

    if(dadosManual){
        dados = dadosManual;
    } else {
        dados = document.getElementById("dados").value
            .split(",")
            .map(Number);
    }

    const res = await fetch("/analisar", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({dados})
    });

    const r = await res.json();

    tabela(r);
    medidas(r);
    graficos(r);
}

// -------- TABELA --------
function tabela(r){
    let t = document.getElementById("tabela");
    t.innerHTML = "";

    r.classes.forEach((c,i)=>{
        t.innerHTML += `
        <tr>
        <td>${c[0]}-${c[1]}</td>
        <td>${r.fi[i]}</td>
        <td>${r.fa[i]}</td>
        <td>${r.xi[i].toFixed(2)}</td>
        <td>${r.fixi[i].toFixed(2)}</td>
        <td>${r.fixi2[i].toFixed(2)}</td>
        </tr>`;
    });
}

// -------- MEDIDAS --------
function medidas(r){
    document.getElementById("medidas").innerHTML = `
    Média: ${r.media}<br>
    Variância: ${r.variancia}<br>
    Desvio Padrão: ${r.dp}<br>
    CV: ${r.cv}%
    `;
}

// -------- GRÁFICOS --------
function graficos(r){

    let labels = r.classes.map(c=>`${c[0]}-${c[1]}`);

    const ctx1 = document.getElementById("hist").getContext("2d");
    const ctx2 = document.getElementById("ogiva").getContext("2d");

    if(chart1) chart1.destroy();

    chart1 = new Chart(ctx1,{
        data:{
            labels: labels,
            datasets:[
                {
                    type:"bar",
                    label:"Frequência",
                    data:r.fi
                },
                {
                    type:"line",
                    label:"Curva Normal",
                    data:r.normal_y,
                    tension:0.4
                }
            ]
        }
    });

    if(chart2) chart2.destroy();

    chart2 = new Chart(ctx2,{
        type:"line",
        data:{
            labels: labels,
            datasets:[{
                label:"Frequência Acumulada",
                data:r.fa
            }]
        }
    });
}

// -------- UPLOAD JSON --------
document.getElementById("fileInput").addEventListener("change", e=>{
    let reader = new FileReader();

    reader.onload = ev=>{
        let json = JSON.parse(ev.target.result);
        analisar(json.dados);
    }

    reader.readAsText(e.target.files[0]);
});

// -------- CATÁLOGO LOCAL --------
async function carregarCatalogo(){
    const res = await fetch("/catalogo");
    const data = await res.json();

    let tipo = document.getElementById("tipoFiltro").value;

    let filtrado = tipo === "todos"
        ? data
        : data.filter(x => x.tipo === tipo);

    analisar(filtrado.map(x=>x.nota));
}

// -------- APIs --------
async function buscarFilmes(){
    let res = await fetch("/tmdb?tipo=movie");
    let data = await res.json();
    analisar(data.map(x=>x.nota));
}

async function buscarSeries(){
    let res = await fetch("/tmdb?tipo=tv");
    let data = await res.json();
    analisar(data.map(x=>x.nota));
}

async function buscarAnime(){
    let res = await fetch("/anime");
    let data = await res.json();
    analisar(data.map(x=>x.nota));
}