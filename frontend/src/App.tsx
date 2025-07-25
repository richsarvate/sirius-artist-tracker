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

const App: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('month');
  const [loading, setLoading] = useState<boolean>(false);
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [expandedArtist, setExpandedArtist] = useState<string | null>(null);
  const [expandedTrack, setExpandedTrack] = useState<{ artist: string; title: string } | null>(null);

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
          const trackBreakdown: Record<string, { count: number; channels: string[] }> = {};
          artist.tracks.forEach((track: any) => {
            if (!trackBreakdown[track.title]) {
              trackBreakdown[track.title] = { count: 0, channels: [] };
            }
            trackBreakdown[track.title].count += track.plays ?? 1;
            if (track.channel && !trackBreakdown[track.title].channels.includes(track.channel)) {
              trackBreakdown[track.title].channels.push(track.channel);
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

  // Replace your Google sign-in useEffect with this:
  useEffect(() => {
    // Only run if not authorized
    if (!isAuthorized) {
      // Helper to render the Google button if the script is loaded
      const renderGoogleButton = () => {
        if (window.google?.accounts?.id) {
          const buttonContainer = document.getElementById("gsi-button");
          if (buttonContainer) {
            buttonContainer.innerHTML = "";
            window.google.accounts.id.renderButton(buttonContainer, {
              theme: "outline",
              size: "large",
              width: 300,
            });
          }
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
        }
      };

      // If the script is already loaded, render immediately
      if (window.google?.accounts?.id) {
        renderGoogleButton();
      } else {
        // Otherwise, wait for the script to load
        const interval = setInterval(() => {
          if (window.google?.accounts?.id) {
            clearInterval(interval);
            renderGoogleButton();
          }
        }, 100);
        // Clean up interval on unmount
        return () => clearInterval(interval);
      }
    }
  }, [isAuthorized]);

  const totalSpins = data.reduce((sum, artist) => sum + artist.count, 0);
  const totalRoyalties = data.reduce((sum, artist) => sum + (artist.count * 20), 0);
  const totalArtists = data.length;

  const handleLogout = () => {
    setIsAuthorized(false);
    window.google.accounts.id.disableAutoSelect();
  };

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
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">SiriusXM Artist Plays Report</h1>
        <button onClick={handleLogout} className="p-2 bg-red-500 text-white rounded">
          Logout
        </button>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Time Period</label>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="p-2 border rounded-md w-full sm:w-48"
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
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center text-gray-600">Loading...</div>
      ) : data.length > 0 ? (
        <div className="overflow-x-auto">
          <div className="grid grid-cols-3 gap-0 mb-2 text-white font-semibold bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-t-lg">
            <div className="text-center">Total Artists: {totalArtists}</div>
            <div className="text-center">Total Spins: {totalSpins.toLocaleString()}</div>
            <div className="text-center">Total Royalties: ${totalRoyalties.toLocaleString()}</div>
          </div>
          <table className="w-full table-auto border-collapse">
            <thead>
              <tr className="bg-gray-200">
                <th className="px-4 py-2 text-left text-gray-700">Artist Name</th>
                <th className="px-4 py-2 text-left text-gray-700">Spins</th>
                <th className="px-4 py-2 text-left text-gray-700">Royalties</th>
              </tr>
            </thead>
            <tbody>
              {data.map((artist, index) => (
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
                          <div className="mb-2 flex items-center gap-2">
                            <span className="text-lg font-semibold text-purple-700">Breakdown</span>
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                              {Object.keys(artist.trackBreakdown).length} tracks
                            </span>
                          </div>
                          <ul className="divide-y divide-purple-100">
                            {Object.entries(artist.trackBreakdown).map(([title, info]) => {
                              const trackInfo = info as { count: number; channels: string[] };
                              return (
                                <li
                                  key={title}
                                  className="flex flex-col"
                                >
                                  <div className="flex justify-between items-center py-1 text-sm">
                                    <span className="truncate text-gray-800 px-4">{title}</span>
                                    <span
                                      className="text-gray-500 px-4 cursor-pointer underline"
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
                                      {trackInfo.count} play{trackInfo.count !== 1 ? "s" : ""}
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
                                              <li key={channel}>{channel}</li>
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

