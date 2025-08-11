import React, { useState, useEffect } from 'react';
import jwt_decode from "jwt-decode";

type GoogleJwtPayload = {
  email: string;
  name: string;
  picture: string;
};

declare global {
  interface Window {
    google: any;
  }
}

const getPreviousDateRange = (period: string) => {
  const now = new Date();

  switch (period) {
    case 'today': {
      // Compare midnight to now today vs midnight to now yesterday
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      const prevDay = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
      const start = new Date(prevDay.getFullYear(), prevDay.getMonth(), prevDay.getDate(), 0, 0, 0);
      const end = new Date(prevDay.getFullYear(), prevDay.getMonth(), prevDay.getDate(), hours, minutes, seconds);
      return { start: start.toISOString(), end: end.toISOString() };
    }
    case 'yesterday': {
      // Compare all of yesterday vs all of the day before
      const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
      const dayBefore = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2);
      const start = new Date(dayBefore.getFullYear(), dayBefore.getMonth(), dayBefore.getDate(), 0, 0, 0);
      const end = new Date(dayBefore.getFullYear(), dayBefore.getMonth(), dayBefore.getDate(), 23, 59, 59);
      return { start: start.toISOString(), end: end.toISOString() };
    }
    case 'week': {
      // Compare from start of this week to now vs same range last week
      const nowDay = now.getDay() === 0 ? 7 : now.getDay(); // Sunday as 7
      const startOfThisWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - nowDay + 1, 0, 0, 0);
      const elapsedMs = now.getTime() - startOfThisWeek.getTime();
      const startOfLastWeek = new Date(startOfThisWeek.getFullYear(), startOfThisWeek.getMonth(), startOfThisWeek.getDate() - 7, 0, 0, 0);
      const endOfLastWeek = new Date(startOfLastWeek.getTime() + elapsedMs);
      return { start: startOfLastWeek.toISOString(), end: endOfLastWeek.toISOString() };
    }
    case 'last-week': {
      // Compare all of last week vs all of the week before
      const nowDay = now.getDay() === 0 ? 7 : now.getDay();
      const startOfThisWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - nowDay + 1, 0, 0, 0);
      const startOfLastWeek = new Date(startOfThisWeek.getFullYear(), startOfThisWeek.getMonth(), startOfThisWeek.getDate() - 7, 0, 0, 0);
      const endOfLastWeek = new Date(startOfThisWeek.getFullYear(), startOfThisWeek.getMonth(), startOfThisWeek.getDate(), 0, 0, 0);
      const startOfWeekBefore = new Date(startOfLastWeek.getFullYear(), startOfLastWeek.getMonth(), startOfLastWeek.getDate() - 7, 0, 0, 0);
      const endOfWeekBefore = new Date(startOfLastWeek.getFullYear(), startOfLastWeek.getMonth(), startOfLastWeek.getDate(), 0, 0, 0);
      return { start: startOfWeekBefore.toISOString(), end: endOfWeekBefore.toISOString() };
    }
    case 'month': {
      // Compare from start of this month to now vs same range last month
      const startOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0);
      const elapsedMs = now.getTime() - startOfThisMonth.getTime();
      const startOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0);
      const endOfLastMonth = new Date(startOfLastMonth.getTime() + elapsedMs);
      return { start: startOfLastMonth.toISOString(), end: endOfLastMonth.toISOString() };
    }
    case 'last-month': {
      // Compare all of last month vs all of the month before
      const startOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0);
      const startOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0);
      const endOfLastMonth = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);
      const startOfMonthBefore = new Date(now.getFullYear(), now.getMonth() - 2, 1, 0, 0, 0);
      const endOfMonthBefore = new Date(now.getFullYear(), now.getMonth() - 1, 0, 23, 59, 59);
      return { start: startOfMonthBefore.toISOString(), end: endOfMonthBefore.toISOString() };
    }
    case 'year': {
      // Compare from start of this year to now vs same range last year
      const startOfThisYear = new Date(now.getFullYear(), 0, 1, 0, 0, 0);
      const elapsedMs = now.getTime() - startOfThisYear.getTime();
      const startOfLastYear = new Date(now.getFullYear() - 1, 0, 1, 0, 0, 0);
      const endOfLastYear = new Date(startOfLastYear.getTime() + elapsedMs);
      return { start: startOfLastYear.toISOString(), end: endOfLastYear.toISOString() };
    }
    case 'last-year': {
      // Compare all of last year vs all of the year before
      const startOfThisYear = new Date(now.getFullYear(), 0, 1, 0, 0, 0);
      const startOfLastYear = new Date(now.getFullYear() - 1, 0, 1, 0, 0, 0);
      const endOfLastYear = new Date(now.getFullYear(), 0, 0, 23, 59, 59);
      const startOfYearBefore = new Date(now.getFullYear() - 2, 0, 1, 0, 0, 0);
      const endOfYearBefore = new Date(now.getFullYear() - 1, 0, 0, 23, 59, 59);
      return { start: startOfYearBefore.toISOString(), end: endOfYearBefore.toISOString() };
    }
    default:
      return null;
  }
};

const App: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('month');
  const [loading, setLoading] = useState<boolean>(false);
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [expandedArtist, setExpandedArtist] = useState<string | null>(null);
  const [expandedTrack, setExpandedTrack] = useState<{ artist: string; title: string } | null>(null);
  const [search, setSearch] = useState<string>("");
  const [previousRoyalties, setPreviousRoyalties] = useState<number | null>(null);

  const getDateRange = (period: string) => {
    console.log('getDateRange period:', period);
    const now = new Date();
    let start;
    let end;

    switch (period) {
      case 'today':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        end = now;
        break;
      case 'yesterday':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'week':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay() + 1);
        end = now;
        break;
      case 'last-week': {
        const startOfThisWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay() + 1);
        start = new Date(startOfThisWeek);
        start.setDate(start.getDate() - 7);
        end = new Date(startOfThisWeek);
        break;
      }
      case 'month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = now;
        break;
      case 'last-month':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        start = new Date(now.getFullYear(), 0, 1);
        end = now;
        break;
      case 'last-year':
        start = new Date(now.getFullYear() - 1, 0, 1);
        end = new Date(now.getFullYear(), 0, 1);
        break;
      case 'all':
      default:
        start = new Date(2020, 0, 1);
        end = now;
        break;
    }

    return { start: start.toISOString(), end: end.toISOString() };
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const { start, end } = getDateRange(period);
      const params = new URLSearchParams({ start, end });
      const response = await fetch(`/api/artist-plays?${params}`);
      const result = await response.json();
      if (result.error) {
        setError(result.error);
        setData([]);
      } else {
        const enrichedData = result.data.map((artist: any) => {
          // For each track, group by title, then by channel, and track last played
          const trackBreakdown: Record<
            string,
            { count: number; channels: { name: string; lastPlayed: string | null }[] }
          > = {};

          artist.tracks.forEach((track: any) => {
            if (!trackBreakdown[track.title]) {
              trackBreakdown[track.title] = { count: 0, channels: [] };
            }
            trackBreakdown[track.title].count += track.plays ?? 1;

            // Find or add channel entry
            let channelEntry = trackBreakdown[track.title].channels.find(
              (c) => c.name === track.channel
            );
            // Optional debug logging
            // console.log("channelEntry before:", channelEntry);
            // console.log("track.timestamp:", track.timestamp);

            if (!channelEntry) {
              trackBreakdown[track.title].channels.push({
                name: track.channel,
                lastPlayed: track.timestamp || null,
              });
            } else {
              if (
                !channelEntry.lastPlayed ||
                (track.timestamp && new Date(track.timestamp) > new Date(channelEntry.lastPlayed))
              ) {
                channelEntry.lastPlayed = track.timestamp;
              }
            }
          });

          return { ...artist, trackBreakdown };
        });
        setData(enrichedData);
      }
    } catch (err) {
      setError('Failed to fetch data');
      setData([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (isAuthorized) {
      fetchData();
    }
  }, [period, isAuthorized]);

  // Replace your existing Google sign-in useEffect with this improved version:
  useEffect(() => {
    // Only run if not authorized
    if (!isAuthorized) {
      // Helper to render the Google button if the script is loaded
      const renderGoogleButton = () => {
        if (window.google?.accounts?.id) {
          const buttonContainer = document.getElementById("gsi-button");
          if (buttonContainer) {
            buttonContainer.innerHTML = "";
            window.google.accounts.id.initialize({
              client_id: "182239299318-an3tmsdprif9pf0bg77ulmfgofkg435h.apps.googleusercontent.com",
              callback: (response: any) => {
                fetch("/api/verify-google-token", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ credential: response.credential }),
                })
                  .then((res) => res.json())
                  .then((data) => {
                    if (data.allowed) {
                      setIsAuthorized(true);
                    } else {
                      alert("Access denied.");
                    }
                  });
              },
            });
            
            window.google.accounts.id.renderButton(buttonContainer, {
              theme: "outline",
              size: "large",
              width: 300,
            });
          }
        }
      };

      // Load the Google Identity Services script if not already loaded
      const loadGoogleScript = () => {
        return new Promise((resolve) => {
          // Check if script is already loaded
          if (window.google?.accounts?.id) {
            resolve(true);
            return;
          }

          // Check if script tag already exists
          const existingScript = document.querySelector('script[src*="accounts.google.com"]');
          if (existingScript) {
            // Script exists but may not be loaded yet, wait for it
            const checkLoaded = setInterval(() => {
              if (window.google?.accounts?.id) {
                clearInterval(checkLoaded);
                resolve(true);
              }
            }, 100);
            return;
          }

          // Create and load the script
          const script = document.createElement('script');
          script.src = 'https://accounts.google.com/gsi/client';
          script.async = true;
          script.defer = true;
          script.onload = () => {
            // Wait a bit for the library to initialize
            setTimeout(() => {
              resolve(true);
            }, 100);
          };
          script.onerror = () => {
            console.error('Failed to load Google Identity Services script');
            resolve(false);
          };
          document.head.appendChild(script);
        });
      };

      // Load script and render button
      loadGoogleScript().then(() => {
        renderGoogleButton();
      });
    }
  }, [isAuthorized]);

  // Filter data by search string
  const filteredData = search.trim()
    ? data.filter(artist =>
        artist.artist.toLowerCase().includes(search.trim().toLowerCase())
      )
    : data;

  // Update summary numbers based on filtered data
  const totalSpins = filteredData.reduce((sum, artist) => sum + artist.count, 0);
  const totalRoyalties = filteredData.reduce((sum, artist) => sum + (artist.count * 20), 0);
  const totalArtists = filteredData.length;

  // Calculate percentage change
  let percentChange: string | null = null;
  if (previousRoyalties !== null && previousRoyalties !== 0 && period !== 'all') {
    const change = ((totalRoyalties - previousRoyalties) / previousRoyalties) * 100;
    percentChange = `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
  }

  const handleLogout = () => {
    setIsAuthorized(false);
    window.google.accounts.id.disableAutoSelect();
  };

  useEffect(() => {
    // Fetch previous period royalties
    const prevRange = getPreviousDateRange(period);
    if (!prevRange) {
      setPreviousRoyalties(null);
      return;
    }
    const fetchPrev = async () => {
      const params = new URLSearchParams(prevRange);
      const response = await fetch(`/api/artist-plays?${params}`);
      const result = await response.json();
      if (result.data) {
        // Filter previous period data by search string, just like filteredData
        const filteredPrev = search.trim()
          ? result.data.filter((artist: any) =>
              artist.artist.toLowerCase().includes(search.trim().toLowerCase())
            )
          : result.data;
        const prevRoyalties = filteredPrev.reduce((sum: number, artist: any) => sum + (artist.count * 20), 0);
        setPreviousRoyalties(prevRoyalties);
      } else {
        setPreviousRoyalties(null);
      }
    };
    fetchPrev();
  }, [period, search]);

  if (!isAuthorized) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
        <div className="bg-white shadow-2xl rounded-2xl p-10 max-w-md w-full text-center">
          <h1 className="text-3xl font-extrabold text-gray-800 mb-4">SiriusXM Reports</h1>
          <p className="text-gray-600 mb-6">Sign in with your Google account</p>
          <div id="gsi-button" className="flex justify-center"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg p-6 mt-6">
      <div className="flex flex-col sm:flex-row sm:justify-between items-center mb-4 gap-4">
        <h1 className="text-2xl font-bold text-gray-800">SiriusXM Artist Spins Report</h1>
        <button onClick={handleLogout} className="p-2 bg-red-500 text-white rounded">
          Logout
        </button>
      </div>
      <div className="mb-4 flex flex-col sm:flex-row gap-4 items-center">
        <input
          type="text"
          className="w-full sm:w-64 p-2 border rounded-md"
          placeholder="Search artist..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="w-full sm:w-48 flex items-center gap-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="p-2 border rounded-md w-full"
            disabled={loading}
          >
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="week">This Week</option>
            <option value="last-week">Last Week</option>
            <option value="month">This Month</option>
            <option value="last-month">Last Month</option>
            <option value="year">This Year</option>
            <option value="last-year">Last Year</option>
            <option value="all">All Time</option>
          </select>
          {percentChange && (
            <span
              className={`text-sm font-semibold ${
                percentChange.startsWith('+')
                  ? 'text-green-600'
                  : percentChange.startsWith('-')
                  ? 'text-red-600'
                  : percentChange === '0.0%' || percentChange === '+0.0%' || percentChange === '-0.0%'
                  ? 'text-gray-500'
                  : ''
              }`}
            >
              {percentChange}
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-0 mb-2 text-white font-semibold bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-t-lg">
        <div className="text-center">Total Artists: {totalArtists}</div>
        <div className="text-center">Total Spins: {totalSpins.toLocaleString()}</div>
        <div className="text-center">Total Royalties: ${totalRoyalties.toLocaleString()}</div>
      </div>
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
      {loading ? (
        <div className="text-center text-gray-600">Loading...</div>
      ) : filteredData.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full table-fixed border-collapse">
            <thead>
              <tr className="bg-gray-200">
                <th className="w-1/2 px-4 py-2 text-left text-gray-700">Artist Name</th>
                <th className="w-1/4 px-4 py-2 text-center text-gray-700">Spins</th>
                <th className="w-1/4 px-4 py-2 text-left text-gray-700">Royalties</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((artist, index) => (
                <React.Fragment key={index}>
                  <tr
                    className="cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => setExpandedArtist(expandedArtist === artist.artist ? null : artist.artist)}
                  >
                    <td className="px-4 py-2 font-medium flex items-center gap-2">
                      <span
                        className={`inline-block transition-transform duration-300 ${
                          expandedArtist === artist.artist ? "rotate-90" : ""
                        }`}
                      >
                        ▶
                      </span>
                      {artist.artist}
                    </td>
                    <td className="px-4 py-2 text-blue-600 underline">{artist.count}</td>
                    <td className="px-4 py-2">${(artist.count * 20).toLocaleString()}</td>
                  </tr>
                  {expandedArtist === artist.artist && (
                    <tr className="bg-gradient-to-r from-blue-50 to-purple-50 transition-all duration-500 ease-in-out">
                      <td colSpan={3} className="px-6 py-4">
                        <div className="overflow-hidden max-h-[500px]">
                          <ul className="divide-y divide-purple-100">
                            {Object.entries(artist.trackBreakdown).map(([title, info]) => {
                              const trackInfo = info as { count: number; channels: { name: string; lastPlayed: string | null }[] };
                              // Find the most recent lastPlayed timestamp across all channels for this track
                              const latestLastPlayed = trackInfo.channels.reduce((latest: string | null, channel) => {
                                if (!channel.lastPlayed) return latest;
                                if (!latest || new Date(channel.lastPlayed) > new Date(latest)) {
                                  return channel.lastPlayed;
                                }
                                return latest;
                              }, null);
                              return (
                                <li key={title}>
                                  <div className="grid grid-cols-2 items-center py-2 px-4 bg-white rounded shadow-sm mb-2">
                                    <span className="truncate text-gray-800 font-medium">{title}</span>
                                    <span
                                      className="text-blue-600 underline cursor-pointer"
                                      onClick={() =>
                                        setExpandedTrack(
                                          expandedTrack &&
                                          expandedTrack.artist === artist.artist &&
                                          expandedTrack.title === title
                                            ? null
                                            : { artist: artist.artist, title }
                                        )
                                      }
                                      title="Show stations"
                                    >
                                      {trackInfo.count}
                                    </span>
                                  </div>
                                  {expandedTrack &&
                                    expandedTrack.artist === artist.artist &&
                                    expandedTrack.title === title && (
                                      <div className="bg-white border border-purple-200 rounded shadow p-3 mt-2 ml-4 w-fit">
                                        <div className="font-semibold text-purple-700 mb-1">Stations:</div>
                                        {trackInfo.channels.length > 0 ? (
                                          <ul className="list-disc list-inside text-gray-700">
                                            {trackInfo.channels.map((channel) => (
                                              <li key={channel.name}>
                                                {channel.name}
                                                <span className="ml-2 text-xs text-gray-500">
                                                  Last Played: {channel.lastPlayed ? new Date(channel.lastPlayed).toLocaleString(undefined, { hour: 'numeric', minute: '2-digit', year: 'numeric', month: 'numeric', day: 'numeric' }) : "N/A"}
                                                </span>
                                              </li>
                                            ))}
                                          </ul>
                                        ) : (
                                          <div className="text-gray-400">No station data</div>
                                        )}
                                      </div>
                                    )}
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center text-gray-600">No data available</div>
      )}
    </div>
  );
};

export default App;

