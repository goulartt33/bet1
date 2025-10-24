const mockPlayers = [
    {
        id: 1,
        name: "LeBron James",
        team: "Los Angeles Lakers",
        position: "SF",
        stats: {
            points: 25.3,
            assists: 7.9,
            rebounds: 7.1,
            threes: 2.2
        },
        last5: [28, 32, 22, 26, 29]
    },
    {
        id: 2,
        name: "Stephen Curry",
        team: "Golden State Warriors",
        position: "PG",
        stats: {
            points: 29.4,
            assists: 6.3,
            rebounds: 6.1,
            threes: 4.9
        },
        last5: [35, 28, 31, 27, 33]
    },
    {
        id: 3,
        name: "Kevin Durant",
        team: "Phoenix Suns",
        position: "SF",
        stats: {
            points: 27.1,
            assists: 5.6,
            rebounds: 6.7,
            threes: 2.1
        },
        last5: [25, 30, 28, 24, 29]
    },
    {
        id: 4,
        name: "Giannis Antetokounmpo",
        team: "Milwaukee Bucks",
        position: "PF",
        stats: {
            points: 31.1,
            assists: 5.7,
            rebounds: 11.8,
            threes: 0.7
        },
        last5: [34, 28, 36, 30, 32]
    },
    {
        id: 5,
        name: "Luka Dončić",
        team: "Dallas Mavericks",
        position: "PG",
        stats: {
            points: 32.4,
            assists: 8.6,
            rebounds: 8.6,
            threes: 3.1
        },
        last5: [35, 40, 28, 33, 30]
    }
];

module.exports = {
    mockPlayers
};