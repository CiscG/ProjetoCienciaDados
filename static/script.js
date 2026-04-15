async function buscarTop50() {
    const btn = document.querySelector(".btn-purple");
    const fonte = document.getElementById("fonteTop").value;
    const campo = document.getElementById("agruparPor").value;
    
    btn.innerText = "⏳ Processando...";
    
    try {
        const res = await fetch(`/buscar_top50?tipo=${fonte}&campo=${campo}`);
        const itens = await res.json();
        
        const resAnalise = await fetch("/analisar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({dados: itens})
        });
        const r = await resAnalise.json();
        renderUI(r);
    } catch (err) {
        alert("Erro de conexão com o servidor Flask.");
    } finally {
        btn.innerText = "⚡ Extrair e Analisar";
    }
}

function renderUI(r) {
    // Tabela de Classes
    document.getElementById("tabela-body").innerHTML = r.classes.map((c, i) => 
        `<tr><td>${c[0]} |- ${c[1]}</td><td>${r.fi[i]}</td><td>${r.fa[i]}</td><td>${r.xi[i]}</td></tr>`
    ).join("");

    // Quadro de Medidas
    document.getElementById("medidas-stats").innerHTML = `
        <div class="stat-item"><b>Média:</b> ${r.media}</div>
        <div class="stat-item"><b>Desvio Padrão:</b> ${r.dp}</div>
        <div class="stat-item"><b>Mediana:</b> ${r.mediana}</div>
        <div class="stat-item"><b>Variância:</b> ${r.variancia}</div>
        <div class="stat-item"><b>Moda:</b> ${r.moda}</div>
        <div class="stat-item"><b>Coef. Variação:</b> ${r.cv}%</div>
        <div class="stat-item"><b>Tamanho (n):</b> ${r.n}</div>
        <div class="stat-item"><b>Amplitude:</b> ${r.at}</div>
    `;

    // Lista de Auditoria
    const tbodyAuditoria = document.querySelector("#tabela-auditoria tbody");
    tbodyAuditoria.innerHTML = r.itens_completos.map(item => 
        `<tr><td>${item.titulo}</td><td>${item.nota}</td><td>${item.ano}</td></tr>`
    ).join("");
}