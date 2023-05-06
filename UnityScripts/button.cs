using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class ButtonScript : MonoBehaviour
{
    public Camera camera1; 
    public Camera camera2; 
    public Camera camera3; 
    public Button switchButton1; 
    public Button switchButton2; 
    public Button switchButton3; 

    public GameObject map;
    public GameObject mapTexture;

    private int activeCameraIndex = 0; //currently active camera

    void Start()
    {
        //add listeners to the button click events
        switchButton1.onClick.AddListener(SwitchToCamera1);
        switchButton2.onClick.AddListener(SwitchToCamera2);
        switchButton3.onClick.AddListener(SwitchToCamera3);

        //activate the first camera and deactivate the others
        ActivateCamera(0);
    }

    void SwitchToCamera1()
    {
        ActivateCamera(0);
    }

    void SwitchToCamera2()
    {
        ActivateCamera(1);
    }

    void SwitchToCamera3()
    {
        ActivateCamera(2);
    }

    void ActivateCamera(int index)
    {
        //deactivate current active camera
        switch (activeCameraIndex)
        {
            case 0:
                camera1.gameObject.SetActive(false);
                mapTexture.SetActive(false);
                break;
            case 1:
                camera2.gameObject.SetActive(false);
                mapTexture.SetActive(false);
                break;
            case 2:
                camera3.gameObject.SetActive(false);
                map.SetActive(true);
                mapTexture.SetActive(false);
                break;
        }

        //activate new camera
        switch (index)
        {
            case 0:
                camera1.gameObject.SetActive(true);
                break;
            case 1:
                camera2.gameObject.SetActive(true);
                break;
            case 2:
                camera3.gameObject.SetActive(true);
                map.SetActive(false);
                mapTexture.SetActive(true);
                break;
        }

        //update active camera index
        activeCameraIndex = index;
    }
}
