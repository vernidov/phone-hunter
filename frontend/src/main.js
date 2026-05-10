console.log("OSINT Phone Hunter Frontend v2.0");
async function searchPhone(phone) {
    const resp = await fetch("http://127.0.0.1:8000/api/v1/search", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({phone})
    });
    return await resp.json();
}
