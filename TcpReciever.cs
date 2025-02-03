using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Newtonsoft.Json;

namespace MediaPipeWebcamModule
{
    public class TcpReceiver
    {
        private readonly TcpListener _listener;
        private readonly BlockingCollection<Dictionary<string, float>> _queue = new(new ConcurrentQueue<Dictionary<string, float>>(), 10);
        private bool _running = true;
        private readonly CancellationTokenSource _cts = new();

        public TcpReceiver(int port)
        {
            _listener = new TcpListener(IPAddress.Loopback, port);
            _listener.Start();
            new Thread(() => ListenForMessages(_cts.Token)).Start();
        }

        private void ListenForMessages(CancellationToken ct)
        {
            try
            {
                while (_running && !ct.IsCancellationRequested)
                {
                    using var client = _listener.AcceptTcpClient();
                    using var stream = client.GetStream();
                    using var reader = new StreamReader(stream, Encoding.UTF8);

                    while (client.Connected && !ct.IsCancellationRequested)
                    {
                        var message = reader.ReadLine();
                        if (string.IsNullOrEmpty(message)) 
                        {
                            Thread.Sleep(30); // Increased delay when idle
                            continue;
                        }

                        var data = JsonConvert.DeserializeObject<Dictionary<string, float>>(message);
                        try
                        {
                            _queue.Add(data, ct); // Will block if queue is full
                        }
                        catch (OperationCanceledException)
                        {
                            break;
                        }
                    }
                }
            }
            catch (Exception ex) when (ex is SocketException || ex is IOException)
            {
                Console.WriteLine($"TCP Error: {ex.Message}");
            }
        }

        public Dictionary<string, float> GetOldestMessage()
        {
            return _queue.TryTake(out var msg, 50) ? msg : null;
        }

        public void Stop()
        {
            _running = false;
            _cts.Cancel();
            _listener.Stop();
            _queue.CompleteAdding();
        }
    }
}