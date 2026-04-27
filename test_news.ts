import YahooFinance from 'yahoo-finance2';
async function test() {
  const yahooFinance = new YahooFinance();
  try {
    const res = await yahooFinance.search('market');
    const res2 = await yahooFinance.search('crypto');
    const news = [...res.news, ...res2.news].sort((a,b) => new Date(b.providerPublishTime).getTime() - new Date(a.providerPublishTime).getTime());
    console.log(news.length);
  } catch (e) {
    console.log(e);
  }
}
test();
