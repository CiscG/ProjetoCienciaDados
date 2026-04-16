let chartH;
let chartO;

async function buscarTop50() {
    const btn = document.querySelector(".btn-purple");
    const fonte = document.getElementById("fonteTop").value;
    const campo = document.getElementById("agruparPor").value;
    
    // Aviso crítico para o usuário devido ao volume gigante de dados
    btn.innerText = "⏳ Baixando milhares de dados... Pode levar de 1 a 5 min. Não feche a página!";
    btn.disabled = true;
    
    try {
        const res = await fetch(`/buscar_top50?tipo=${fonte}&campo=${campo}`);
        const itens = await res.json();
        
        btn.innerText = "📈 Analisando Estatísticas...";
        
        const resAnalise = await fetch("/analisar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({dados: itens})
        });
        const r = await resAnalise.json();
        
        if (r.erro) {
            alert(r.erro);
            return;
        }
        
        renderUI(r);
    } catch (err) {
        alert("Erro de conexão ou timeout do servidor. Verifique o terminal do Python.");
        console.error(err);
    } finally {
        btn.innerText = "⚡ Extrair e Analisar";
        btn.disabled = false;
    }
}

function renderUI(r) {
    document.getElementById("tabela-body").innerHTML = r.classes.map((c, i) => 
        `<tr><td>${c[0]} |- ${c[1]}</td><td>${r.fi[i]}</td><td>${r.fa[i]}</td><td>${r.xi[i]}</td></tr>`
    ).join("");

    document.getElementById("medidas-stats").innerHTML = `
        <div class="stat-item"><b>Média:</b> ${r.media}</div>
        <div class="stat-item"><b>Desvio Padrão:</b> ${r.dp}</div>
        <div class="stat-item"><b>Variância:</b> ${r.variancia}</div>
        <div class="stat-item"><b>Coef. Variação:</b> ${r.cv.toFixed(2)}%</div>
        <div class="stat-item"><b>Mediana:</b> ${r.mediana}</div>
        <div class="stat-item"><b>Moda:</b> ${r.moda}</div>
        <div class="stat-item"><b>Tamanho (n):</b> ${r.n}</div>
        <div class="stat-item"><b>Amplitude (h):</b> ${r.h}</div>
        <div class="stat-item" style="grid-column: 1 / -1; background: #e0e7ff; border-left-color: #4f46e5;">
            <b>Regra da Raiz (K):</b> ${r.k} Classes
        </div>
    `;

    const tbodyAuditoria = document.querySelector("#tabela-auditoria tbody");
    tbodyAuditoria.innerHTML = r.itens_completos.map(item => 
        `<tr><td>${item.titulo}</td><td>${item.nota}</td><td>${item.ano}</td></tr>`
    ).join("");

    const labels = r.classes.map(c => `${c[0]}-${c[1]}`);

    const ctx = document.getElementById("histChart").getContext("2d");
    if(chartH) chartH.destroy();
    chartH = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequência (fi)',
                data: r.fi,
                backgroundColor: '#8b5cf6'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    const ctxO = document.getElementById("ogivaChart").getContext("2d");
    if (chartO) chartO.destroy();
    chartO = new Chart(ctxO, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequência Acumulada (fa)',
                data: r.fa,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.1,
                pointRadius: 2,
                pointBackgroundColor: '#ef4444'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    // Removemos o limite rígido de max: 50, pois o N agora é gigante (7184 ou 9521)
                    title: { display: true, text: 'Frequência Acumulada' }
                }
            }
        }
    });
}