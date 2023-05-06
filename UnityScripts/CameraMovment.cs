using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraMovment : MonoBehaviour
{
    public float speed = 10f; 
    public float dragSpeed = 2f;
    public float smoothing = 5f; 
    public float rotationSpeed = 100f;

    private Vector3 dragOrigin; 
    private Vector3 targetPosition; 

    void Update()
    {
        //check for mouse input
        if (Input.GetMouseButtonDown(0))
        {
            //save mouse position as the starting point of dragging
            dragOrigin = Input.mousePosition;
        }

        if (Input.GetMouseButton(0))
        {
            //calculate how much the mouse has moved since dragging started
            Vector3 mouseDelta = Input.mousePosition - dragOrigin;

            //calculate the movement vector based on the mouse movement
            Vector3 movement = new Vector3(mouseDelta.x, 0f, mouseDelta.y);

            movement = transform.TransformDirection(movement);
            movement.y = 0f;

            //calculate the target position based on the movement and speed
            targetPosition = transform.position + movement * dragSpeed * Time.fixedDeltaTime;
        }

        if (Input.GetMouseButton(1))
        {
            //get the horizontal movement of the mouse and rotate the camera around its y axis
            float rotation = Input.GetAxis("Mouse X") * rotationSpeed * Time.fixedDeltaTime;
            transform.Rotate(0f, -rotation, 0f, Space.World);
        }

        //if not dragging or rotating, smoothly move the camera towards the target position
        if (!Input.GetMouseButton(0))
        {
            targetPosition = transform.position;

            if (Input.GetKey(KeyCode.W))
            {
                targetPosition += transform.forward * speed * Time.fixedDeltaTime;
            }

            if (Input.GetKey(KeyCode.A))
            {
                targetPosition += -transform.right * speed * Time.fixedDeltaTime;
            }

            if (Input.GetKey(KeyCode.S))
            {
                targetPosition += -transform.forward * speed * Time.fixedDeltaTime;
            }

            if (Input.GetKey(KeyCode.D))
            {
                targetPosition += transform.right * speed * Time.fixedDeltaTime;
            }
        }

        transform.position = Vector3.Lerp(transform.position, targetPosition, smoothing * Time.fixedDeltaTime);
    }
}
