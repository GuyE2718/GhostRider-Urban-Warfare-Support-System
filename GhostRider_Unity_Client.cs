using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.IO;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using UnityEngine.UI;

public class scripttest : MonoBehaviour
{
    static string HOST = "localhost";
    static int PORT = 12345;
    static string PASSCODE = "mypassword";
    public static byte[] IV;
    public static byte[] KEY; 

    private TcpClient clientSocket;
    private NetworkStream networkStream;

    public bool click = false;
    public Marker marker;
    public Image canvasImage;
    public Sprite load;
    public Sprite main;
    public GameObject buttons;

    public GameObject[] logins;

    private void Start()
    {
        buttons.SetActive(false);
        canvasImage.sprite = load;
        Connect();
    }


    async void Connect()
    {
        if (click)
        {
            clientSocket = new TcpClient();

            while (!clientSocket.Connected)
            {
                try
                {
                    //attempt to connect to the server
                    await clientSocket.ConnectAsync(HOST, PORT);
                }
                catch (SocketException)
                {
                    //connection failed, wait 1 second and try again
                    await Task.Delay(1000);
                }
            }

            //send the passcode for authentication
            networkStream = clientSocket.GetStream();
            byte[] passcodeBytes = Encoding.ASCII.GetBytes(PASSCODE);
            await networkStream.WriteAsync(passcodeBytes, 0, passcodeBytes.Length);

            for (int i = 0; i < logins.Length; i++)
            {
                logins[i].SetActive(false);
            }
            canvasImage.sprite = main;
            buttons.SetActive(true);
            //start a new thread to receive and process the data
            await Task.Run(ProcessData);
        }
        
    }

    async void ProcessData()
    {
        byte[] data = new byte[1024];
        int bytesRead;

        while ((bytesRead = await networkStream.ReadAsync(data, 0, data.Length)) > 0)
        {
            //decrypt the data
            byte[] decryptedData = Decrypt(data, bytesRead);
            Debug.Log($"Received data (bytes): {BitConverter.ToString(decryptedData)}");
            string unpaddedData = Encoding.UTF8.GetString(decryptedData);
            Debug.Log($"Received data (string): {unpaddedData}");

            //call makeMarker function from the Marker script using MainThreadDispatcher
            UnityMainTheadDispatcher.Instance().Enqueue(() => marker.makeMarker(unpaddedData));

            byte[] response = Encoding.ASCII.GetBytes("OK");
            byte[] encryptedResponse = Encrypt(response);
            await networkStream.WriteAsync(encryptedResponse, 0, encryptedResponse.Length);
        }
    }

    static byte[] Decrypt(byte[] data, int count)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = KEY;
            aes.IV = IV;
            aes.Padding = PaddingMode.PKCS7;
            aes.Mode = CipherMode.CBC;

            using (MemoryStream ms = new MemoryStream(data, 0, count))
            using (CryptoStream cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Read))
            {
                byte[] decryptedData = new byte[count];
                int decryptedDataLength = cs.Read(decryptedData, 0, decryptedData.Length);
                Array.Resize(ref decryptedData, decryptedDataLength);
                return decryptedData;
            }
        }
    }

    public void clickboolactive()
    {
        click = true;
        Connect();
    }

    static byte[] Encrypt(byte[] data)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = KEY;
            aes.IV = IV;
            aes.Padding = PaddingMode.PKCS7;
            aes.Mode = CipherMode.CBC;

            using (MemoryStream ms = new MemoryStream())
            using (CryptoStream cs = new CryptoStream(ms, aes.CreateEncryptor(), CryptoStreamMode.Write))
            {
                cs.Write(data, 0, data.Length);
                cs.FlushFinalBlock();
                return ms.ToArray();
            }
        }
    }
}
