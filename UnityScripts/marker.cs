using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Marker : MonoBehaviour
{
    public GameObject marker;
    public Transform markerpos;
    public bool markneed = false;
    public GameObject pointGrid;


    public void makeMarker(string unpaddedData)
    {
        foreach (Transform point in pointGrid.transform)
        {
            GameObject pointchild = point.gameObject;
            if (unpaddedData == pointchild.name)
            {
                GameObject mark = Instantiate(marker, pointchild.transform.position, marker.transform.rotation);
                mark.name = unpaddedData;
                Debug.Log("mark placed");
            }
            else
            {
                Debug.Log("mark not placed");
            }
        }
        
    }
}
